(function($, window) {

window.searchMap = (function() {
  var config = {
    map_wrapper_selector: '.map-wrapper',
    results_page: false,
    results_container_selector: '#results-container'
  };
  var map;
  var $map_wrapper;
  var $form;
  var $latlng_panel;
  var $results_btn;

  // add handlers to the provided
  // - form
  // - map
  // elements
  var addHandlers = function() {
    $form.on("submit", function(e) {
      indicatePerformingGeocode();
      geoUtils.performGeocode($form.find(".location").val(), queryGeocodeCallback);
      e.preventDefault();
    });

    map.on('click', function(e){
      indicatePerformingGeocode();
      $form.find(".location").val("");
      updateLinkURL( e.latlng.lat, e.latlng.lng );
      geoUtils.performReverseGeocode(e.latlng.lat, e.latlng.lng, function(data) {
        updateMapFocus(data, true);
      });
    });
  };

  // performs the search
  // returns html to be inserted
  var doSearch = function(lat, lng, url) {
    var url = url || generateURL(lat, lng);
    $.ajax({
      type: "GET",
      url: url,
      contentType: "text/html; charset=utf-8",
      success: function(data) {
        $( config.results_container_selector ).html(data);
        window.history.pushState({}, "current search", "/about-an-area?latitude="+lat+"&longitude="+lng);
      }
    });
  };

  // get DOM elements using the
  // provided selectors
  var fetchElements = function() {
    $form = $( config.form_selector );
    $latlng_panel = $( config.latlng_panel_selector );
    $map_wrapper = $( config.map_wrapper_selector );
    $results_btn = $( config.result_btn_selector );
  };

  // generate the URL for the area query
  var generateURL = function(lat, lng) {
    if( config.results_page ) return "/about-an-area-query?latitude="+lat+"&longitude="+lng;
    return  "/about-an-area?latitude="+lat+"&longitude="+lng;
  };

  var indicatePerformingGeocode = function(state) {
    if(state === "finished") {
      $map_wrapper.removeClass("performing-geocode");
      $results_btn.attr("disabled", false);
    } else {
      $map_wrapper.addClass("performing-geocode");
      $results_btn.attr("disabled", true);
    }
  };

  // render the Leaflet map
  // add marker in current focused position
  var renderMap = function(lat, lng) {
    map = dslMapUtils
            .renderLeafletMap( config.map_selector )
            .setView([lat, lng], 12);

    query_marker = dslMapUtils.addMarkerToMap(map, lat, lng);
  };

  // callback for any geocode query performed
  // - shows any errors if geocode fails
  // - calls update function if successful
  var queryGeocodeCallback = function(data) {
    var $location_input = $form.find(".location"),
        $form_group = $form.find(".form-group-search");

    if( data.success ) {
      $location_input.removeClass("form-control-error");
      $form_group.removeClass("form-group-error");
      updateMapFocus(data, true);
    } else {
      $form_group.addClass("form-group-error");
      $location_input.addClass("form-control-error");
      indicatePerformingGeocode("finished");
    }
  };

  // updates
  // - the latlng panel
  // - map and marker position
  var updateLatLngPanel = function(data) {
		var $query_meta = $latlng_panel.find(".query-meta").show();

		if( data.query ) {
			$latlng_panel
        .find(".display-query")
        .text( data.query );
		} else if (data.address) {
      $latlng_panel
        .find(".display-query")
        .text( data.address );
    } else {
			$query_meta.hide();
		}

		$latlng_panel
      .find(".display-lat")
      .text( geoUtils.roundLatLng(data.lat, 5) );
		$latlng_panel
      .find(".display-lng")
      .text( geoUtils.roundLatLng(data.lng, 5) );

	};

  // update the link that will load the results
  var updateLinkURL = function(lat, lng) {
    var url = generateURL(lat, lng);
    $results_btn
      .attr("href", url)
      .removeClass("disabled");

    if( config.results_page ) {
      $results_btn.off('click');
      $results_btn.click(function(e){
        e.preventDefault();
        doSearch(lat, lng, url);
      });
    }
  };

  var updateMarkerPos = function(data, pan) {
    var pan = pan || false;
    dslMapUtils.updateMarkerPos(query_marker, map, data.lat, data.lng, pan);
  };

	var updateMapFocus = function(data, pan) {
		updateLatLngPanel(data);
    updateMarkerPos(data, pan);
		updateLinkURL(data.lat, data.lng);
    indicatePerformingGeocode("finished");
	};

  // init function
  // sets up the search map component
  var init = function(settings) {
    $.extend( config, settings );

    // use jQuery to get refs to required els
    fetchElements();

    renderMap(config.place.lat, config.place.lng);
    updateMapFocus(config.place);

    addHandlers();

    if( config.results_page ) {
      doSearch(config.place.lat, config.place.lng)
    }
  };

  return {
    initializeMap: init,
    updateFocus: updateMapFocus
  }
})();

}).call(this, jQuery, window);