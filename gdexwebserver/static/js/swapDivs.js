function swapDivs(hide,show) {
  var icon="I"+hide;
  var main_div=document.getElementById("D"+hide);
  var icon_div=document.getElementById(icon);
  if (icon_div) {
    icon_div.style.visibility="hidden";
    icon_div.style.position="absolute";
  }
  main_div.style.visibility="hidden";
  main_div.style.position="absolute";
  main_div.style.left="0px";
  var icon="I"+show;
  var main_div=document.getElementById("D"+show);
  var icon_div=document.getElementById(icon);
  if (icon_div) {
    if (hide < show) {
	icon_div.style.visibility="visible";
	icon_div.style.position="relative";
    }
    else {
	icon_div.removeAttribute("style");
    }
  }
  if (hide < show) {
    main_div.style.visibility="visible";
    main_div.style.position="relative";
  }
  else {
    main_div.removeAttribute("style");
  }
}
