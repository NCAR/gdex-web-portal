# GDEX Web Portal

This project contains the Python Django framework supporting the [NSF NCAR Geoscience Data Exchange (GDEX)](https://gdex.ucar.edu) data portal.

## Backups

The `gdexdata` PVC is backed up nightly to S3. See [BACKUP.md](./BACKUP.md) for the backup configuration and restore procedures (both single-file and full-PVC).