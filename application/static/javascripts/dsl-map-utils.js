var dslMapUtils = (function() {
  var config = {};

  /* Given map
	   create marker at lat and lng
	   return marker ref */
  var addMarkerToMap = function(map, lat, lng) {
      var marker = L.marker([lat, lng]);
      map.addLayer(marker);
      return marker;
  };

  var removeMarkerFromMap = function(marker, map) {
    if( marker ) {
      map.removeLayer( marker );
    }
  };

  /* Update a marker position on a map
      marker: an existing marker object
      Lmap: a leaflet map
      lat: new latitude
      lng: new longitude
      pan: [Bool] if you want map to pan to new marker */
  var updateMarkerPos = function(marker, Lmap, lat, lng, pan) {
    marker.setLatLng([lat, lng]);
    if ( pan ) {
      Lmap.panTo(new L.LatLng(lat, lng));
    }
  };

  /* render a basic leaflet map
      takes #id for the map
      and any leaflet options */
  var renderLeafletMap = function(map_element_id, options) {
    var options = options || {};
    var Lmap = L.map(map_element_id, options);
    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token='+this.config.mapbox_token, {
      attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
      maxZoom: 18,
      id: 'mapbox.streets',
      accessToken: this.config.mapbox_token
    }).addTo(Lmap);
    return Lmap;
  };


  var init = function(settings) {
    this.config = settings;
    // only expose once mapbox token is set
    if(this.config.mapbox_token) this.renderLeafletMap = renderLeafletMap;
  };

  return {
    init: init,
    addMarkerToMap: addMarkerToMap,
    removeMarkerFromMap: removeMarkerFromMap,
    updateMarkerPos: updateMarkerPos
  }
})();
