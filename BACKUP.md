# Backup and Restore

The `gdexdata` PVC is backed up nightly to the GDEX S3 appliance
(`https://boreas.hpc.ucar.edu:6443`, bucket `gdex`, prefix
`gdex-web-data/`) via a Kubernetes CronJob defined in the chart.

This document describes how the backup works and how to restore from
it, both for a single file at a point in time and for a full PVC.

## Overview

| Component         | Where                                                    |
|-------------------|----------------------------------------------------------|
| Source data       | `gdexdata` PVC mounted at `/data` in the web pods        |
| Destination       | `s3://gdex/gdex-web-data/` on the GDEX appliance         |
| Schedule          | 02:17 UTC nightly (configured via `backup.schedule`)     |
| Credentials       | `backup-s3-creds` secret in the deployment namespace     |
| Bucket versioning | Enabled — overwrites and deletes retain previous bytes   |
| Lifecycle policy  | Noncurrent versions expire after 90 days                 |
| Tool              | `rclone copy` (never `sync`; deletions don't propagate)  |
| Run reports       | `s3://gdex/gdex-web-data/_reports/<run-id>.txt` per run  |

The CronJob template lives at `app-chart/templates/pv-s3-backup.yaml`
and is gated by `backup.enabled` in values. Test deployments
(`--set testName=...`) skip the CronJob automatically so they don't
write to the production backup prefix.

## What's in the backup

Almost everything readable under `/data`. A few exceptions worth knowing:

- **Symlinks are preserved as symlinks** (`--links`). They're stored
  in S3 as small `.rclonelink` placeholder files containing the target
  path; on restore (with rclone, also using `--links`) they're
  recreated as real symlinks. Both in-tree symlinks (like the
  LevelTables aliases) and broken absolute-path symlinks (like the
  `/glade` one) round-trip faithfully — the restored PV matches the
  source layout, including its broken links.
- **Permission-denied paths are logged and tolerated.** The backup pod
  runs as UID 33 (matches PVC ownership), so this shouldn't happen in
  practice, but the report would surface any cases.

The run report at `_reports/<run-id>.txt` always lists what was
skipped, even on otherwise-successful runs.

## How the CronJob decides success or failure

| rclone exit | Other errors | Job result | Meaning                          |
|-------------|--------------|------------|----------------------------------|
| 0           | 0            | Success    | Clean run                        |
| 6           | 0            | Success    | Only expected errors (see report)|
| anything else | -          | Fail       | Real problem — Alertmanager fires|

"Expected errors" means permission-denied paths or broken symlinks.
Anything else (network failures, auth errors, the appliance being
unreachable, etc.) fails the Job loudly.

## Restoring a single file

Use this when one file got corrupted, accidentally modified, or
deleted on the live PVC, and you want a clean copy from S3.

### The current backed-up version

The simplest case. From a pod with rclone and the backup credentials
(easiest: spin up a debug pod modeled on the CronJob, or use any pod
where `rclone` and the secret are available):

```sh
rclone copy \
  gdex:gdex/gdex-web-data/path/to/file.xml \
  /tmp/restored/
```

Then move it into place on the PVC, with whatever ownership/mode the
original had:

```sh
chown 33:33 /tmp/restored/file.xml
cp -p /tmp/restored/file.xml /data/path/to/file.xml
```

### An older version (point-in-time restore)

Because bucket versioning is enabled, every overwrite or delete keeps
the previous bytes for up to 90 days. To restore a specific historical
version, use boto3 or the AWS CLI — rclone doesn't have great
version-aware support.

```sh
export AWS_ACCESS_KEY_ID=$(kubectl get secret backup-s3-creds \
  -o jsonpath='{.data.access_key}' | base64 -d)
export AWS_SECRET_ACCESS_KEY=$(kubectl get secret backup-s3-creds \
  -o jsonpath='{.data.secret_key}' | base64 -d)
export AWS_DEFAULT_REGION=us-east-1
ENDPOINT=https://boreas.hpc.ucar.edu:6443

# List all versions of a specific object
aws --endpoint-url "${ENDPOINT}" s3api list-object-versions \
  --bucket gdex \
  --prefix gdex-web-data/path/to/file.xml

# Output includes Versions[] (each with VersionId, LastModified, Size)
# and DeleteMarkers[] if the object was deleted. Pick the VersionId
# you want, then:

aws --endpoint-url "${ENDPOINT}" s3api get-object \
  --bucket gdex \
  --key gdex-web-data/path/to/file.xml \
  --version-id "<the-version-id>" \
  /tmp/restored-file.xml
```

Notes:

- `IsLatest: true` is the current version. Older versions have
  `IsLatest: false`.
- A delete marker means the object was deleted via `rclone sync` or
  similar. We don't issue deletes from the backup process, but a
  manual purge would create one. The object's content lives in the
  prior version, accessible by VersionId.
- Versions older than ~90 days may have been removed by the lifecycle
  policy. If you need longer retention for a specific file, copy it
  somewhere else.

## Restoring the entire PVC

Use this for catastrophic data loss — the underlying PV is gone, the
PVC is corrupted, or someone ran something they shouldn't have.

### Prerequisites

- A new (empty) PVC of sufficient size. The current `gdexdata` is 2Ti.
- The `backup-s3-creds` secret in the same namespace.
- Roughly an hour of patience (depends on link to the appliance; the
  initial seed of ~55 GiB took about an hour over the appliance link).

### Procedure

1. Provision the replacement PVC. Use the same name (`gdexdata`) or
   pick a temporary one and rename later.

2. Run a restore pod that mounts the new PVC and runs rclone in the
   reverse direction. A minimal manifest:

   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: gdex-restore
     namespace: rda
   spec:
     restartPolicy: Never
     securityContext:
       runAsNonRoot: true
       runAsUser: 33
       runAsGroup: 33
       fsGroup: 33
     containers:
       - name: rclone
         image: docker.io/rclone/rclone:1.74
         command: ["/bin/sh", "-c"]
         args:
           - |
             set -eu
             export RCLONE_CONFIG=/tmp/rclone.conf
             cat > "${RCLONE_CONFIG}" <<EOF
             [src]
             type = s3
             provider = Other
             endpoint = https://boreas.hpc.ucar.edu:6443
             force_path_style = true
             env_auth = true
             EOF
             rclone copy \
               --links \
               --transfers 8 \
               --checkers 16 \
               --s3-chunk-size 64M \
               --stats 1m \
               --stats-one-line \
               --metadata \
               src:gdex/gdex-web-data/ /data/
         env:
           - name: AWS_ACCESS_KEY_ID
             valueFrom:
               secretKeyRef: { name: backup-s3-creds, key: access_key }
           - name: AWS_SECRET_ACCESS_KEY
             valueFrom:
               secretKeyRef: { name: backup-s3-creds, key: secret_key }
         volumeMounts:
           - name: target
             mountPath: /data
         resources:
           requests: { cpu: "200m", memory: "256Mi" }
           limits:   { cpu: "2",    memory: "6Gi"   }
     volumes:
       - name: target
         persistentVolumeClaim:
           claimName: gdexdata
   ```

3. Monitor progress:

   ```sh
   kubectl logs -f -n rda gdex-restore
   ```

4. When rclone exits 0, verify:

   ```sh
   # File count and size should match the backup
   kubectl exec gdex-restore -- du -sh /data
   kubectl exec gdex-restore -- find /data -type f | wc -l
   ```

5. Delete the restore pod and bring the application back up against
   the restored PVC.

### What you DON'T get back from a restore

- **POSIX mode bits.** S3 doesn't store them. Restored files will have
  the umask defaults of the restore pod. If the app cares about
  specific modes (e.g., the `700` directories under `web/datasets/`),
  those need to be re-applied separately.
- **Ownership across UIDs.** If the restore pod runs as UID 33,
  everything comes back owned by 33:33 (which is correct). If the
  pod runs as anything else, you'll need a `chown -R 33:33 /data`
  after restore.

Symlinks DO come back as symlinks (including the broken `/glade`
one, in the same state as the source), provided the restore is done
with rclone using the `--links` flag — see the example manifest above.

## Testing the restore

The restore procedure is only as good as the last time you tested
it. Recommended: do a quarterly restore drill into a throwaway PVC,
spot-check a handful of files, then tear down the test PVC. Calendar
reminder, not optional.

## Operational notes

- **First-time backup setup** including the manual seed, lifecycle
  policy, and bucket versioning configuration was done out-of-band
  and is not re-applied by the chart. If the bucket itself is ever
  recreated, those steps need to be redone
- **Schedule conflicts.** If multiple charts in the cluster eventually
  back up to the same appliance at the same time, the link could
  saturate. The CronJob defaults to 02:17 UTC; stagger via
  `backup.schedule` in per-chart values if this becomes a problem.
- **Run reports** are uploaded to `_reports/` even on successful
  runs. They list any permission-denied paths and broken symlinks
  encountered, which is useful for spotting source-side issues
  (newly-locked directories, broken symlinks) without having to
  trawl the Loki logs.
- **rclone version bumps.** The image tag is pinned in the chart
  defaults. Don't use `:latest` or `:master` — rolling tags break
  unattended jobs in surprising ways.