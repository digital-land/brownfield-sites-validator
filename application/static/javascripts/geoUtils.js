// requires: jQuery

var geoUtils = (function($) {
  var config = {};

  /* reduce lat or lng number to desirable
     number of decimal places */
  var roundLatLng = function(latlng, decs) {
	  return parseFloat(latlng.toFixed(decs));
  };

  // attempts to geocode the query
  var performGeocode = function(queryStr, cb) {
    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: this.config.urls.geocode,
        data: JSON.stringify({query: queryStr}),
        success: cb,
        dataType: "json"
    });
  };

  // attempts to obtain an address from lat, lng coords
  var performReverseGeocode = function(lat, lng, cb) {
    $.ajax({
      type: "POST",
      contentType: "application/json; charset=utf-8",
      url: this.config.urls.reversegeocode,
      data: JSON.stringify({lat: lat, lng: lng}),
      success: cb,
      dataType: "json"
    });
  };

  var init = function(settings) {
    this.config = settings;
    // only expose once url endpoints are set
    if(this.config.urls.geocode) this.performGeocode = performGeocode;
    if(this.config.urls.reversegeocode) this.performReverseGeocode = performReverseGeocode;
  }

  return {
    init: init,
    roundLatLng: roundLatLng
  }

}).call(this, jQuery);
