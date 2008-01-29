// Define a new map tile layer.
// ============================
// You need to turn this layer on once your map loads with code like this:
//
//   map.addOverlay(new GTileLayerOverlay(gheat));

bounds = new GLatLngBounds(new GLatLng(-90, -180), new GLatLng(90, 180));
copyright = new GCopyright( 'your-org-copyright'
                          , bounds
                          , 0
                          , "(©) 2007 Your Org <www.example.com>"
                           );
copyrights = new GCopyrightCollection();
copyrights.addCopyright(copyright);
gheat = new GTileLayer(copyrights, 10, 0);
gheat.getTileUrl = function (tile, zoom) {
  base = "http://localhost:8080";
  url = base +'/'+ zoom +'/'+ tile.x +','+ tile.y +'.png';
  return url;
}
gheat.isPng = function () {return true;}
gheat.getOpacity = function () {return 1.0;}

alert(gheat.getTileUrl({x:4,y:6},4));
