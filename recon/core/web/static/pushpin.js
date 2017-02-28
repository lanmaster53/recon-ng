var map
var bounds
var icons = {
    default: 'ffffff',
    flickr: 'ff8000',
    instagram: 'ffc0cb',
    picasa: '984c99',
    shodan: 'ffff00',
    twitter: '32cdff',
    youtube: 'e62117',
}

function load_map() {
    var coords = new google.maps.LatLng(0,0);
    var mapOptions = {
        zoom: 5,
        center: coords,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        disableDefaultUI: true,
        mapTypeControl: true,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
            position: google.maps.ControlPosition.RIGHT_TOP
        },
        panControl: true,
        panControlOptions: {
            position: google.maps.ControlPosition.RIGHT_BOTTOM
        },
        streetViewControl: true,
        streetViewControlOptions: {
            position: google.maps.ControlPosition.RIGHT_BOTTOM
        },
        zoomControl: true,
        zoomControlOptions: {
            position: google.maps.ControlPosition.RIGHT_BOTTOM
        },
    };
    map = new google.maps.Map(document.getElementById("map"), mapOptions);
    bounds = new google.maps.LatLngBounds();
}

function add_marker(opts, place, pushpin) {
    var marker = new google.maps.Marker(opts);
    var infowindow = new google.maps.InfoWindow({
        autoScroll: false,
        content: place.details
    });
    google.maps.event.addListener(marker, 'click', function() {
        infowindow.open(map, marker);
    });
    // add the pushpin data to its marker object
    marker.pushpin = pushpin;
    window['markers'].push(marker);
    bounds.extend(opts.position);
    return marker;
}

function load_markers(json) {
    var sources = [];
    for (var i = 0; i < json['rows'].length; i++) {
        pushpin = json['rows'][i];
        // add the marker to the map
        var color = icons[pushpin.source.toLowerCase()] || icons['default'];
        var marker = add_marker({
            position: new google.maps.LatLng(pushpin.latitude, pushpin.longitude),
            title: pushpin.profile_name,
            icon: 'http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|'+color,
            map: map,
        },{
            details:'<table class="iw-content">'
                + '<caption><a href="'+pushpin.profile_url+'" target="_blank">'+pushpin.profile_name+'</a></caption>'
                + '<tr><td>Handle</td><td>'+pushpin.screen_name+'</td></tr>'
                + '<tr><td>Message</td><td>'+pushpin.message+'</td></tr>'
                + '<tr><td>Time</td><td>'+pushpin.time+'</td></tr>'
                + '<tr><td colspan="2"><a href="'+pushpin.media_url+'" target="_blank"><img src="'+pushpin.thumb_url+'" /></a></td></tr>'
                + '</table>'
        },
            pushpin
        );
        // add filter checkboxes for each unique source
        if (sources.indexOf(pushpin.source) === -1) {
            var checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'source';
            checkbox.value = pushpin.source;
            checkbox.setAttribute('checked', 'checked');
            checkbox.checked = true;
            checkbox.addEventListener('change', function(e) {
                toggle_marker(e.target);
            });
            var filter = document.getElementById('filter-source');
            filter.appendChild(checkbox);
            filter.appendChild(document.createTextNode(' '+pushpin.source));
            filter.appendChild(document.createElement('br'));
            sources.push(pushpin.source);
        }
    }
    map.fitBounds(bounds);
}

// set the map on all markers in the array
function toggle_marker(element) {
    _map = null;
    if(element.checked) {
        _map = map;
    }
    for (var i = 0; i < window['markers'].length; i++) {
        if (window['markers'][i].pushpin[element.name] === element.value) {
            window['markers'][i].setMap(_map);
        }
    }
}

$(document).ready(function() {
    // load the map
    load_map();
    // build the url
    var url = "/api/workspaces/"+workspace+"/tables/pushpins";
    // load the pushpins
    $.ajax({
        type: "GET",
        url: url,
        success: function(data) {
            // declare a storage array for markers
            window['markers'] = [];
            load_markers(data);
            console.log("Markers loaded successfully.");
        },
        error: function(error) {
            console.log(error);
        }
    });
});
