// This Script is taken (and slightly modified) from href="http://www.web-toolbox.net/webtoolbox/dhtml/info-box01/info-box01.htm"

var offsetx=20
var offsety=0

function HideInfoBox() {
    document.getElementById('InfoBox').style.visibility = "hidden";
}

function ShowInfoBox(e,content,offsetX,offsetY)
{
    if (offsetX) {offsetx=offsetX;} else {offsetx=20;}
    if (offsetY) {offsety=offsetY;} else {offsety=0;}
    var PositionX = 0;
    var PositionY = 0;
    if (!e) var e = window.event;
    if (e.pageX || e.pageY)
    {
	PositionX = e.pageX;
	PositionY = e.pageY;
    }
    else if (e.clientX || e.clientY)
    {
	PositionX = e.clientX + document.body.scrollLeft;
	PositionY = e.clientY + document.body.scrollTop;
    }
    
    document.getElementById("BoxContent").innerHTML = content;
    document.getElementById('InfoBox').style.left = (PositionX+offsetx)+"px";
    document.getElementById('InfoBox').style.top = (PositionY+offsety)+"px";
    document.getElementById('InfoBox').style.visibility = "visible";
}
