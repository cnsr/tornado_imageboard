var map = L.map( 'map', {
    center: [20.0, 5.0],
    minZoom: 2,
    zoom: 2
});

L.tileLayer( 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    subdomains: ['a','b','c']
}).addTo( map );

$(document).ready(function(){
	getPosters();
});

$.ajaxSettings.traditional = true;
function getPosters() {
	$.ajax({
		url : "/ajax/map/",
		type : "POST",
		data : {_xsrf: getCookie("_xsrf")},
		success : function(json) {
			var json = jQuery.parseJSON(json);
			$.each(json, function( index, value ) {
				let poster = json[index];
				let icon = L.icon({
					iconUrl: "/flags/" + poster.country  + ".png",
					iconRetinaUrl: "/flags/" + poster.country  + ".png",
					iconSize: [24, 24],
					iconAnchor: [9, 21],
					popupAnchor: [0, -14]
				});
				L.marker([poster.lat, poster.long], {icon: icon})
				  .bindPopup( '<span>Last posted:<br />' + poster.date.split(' ')[0] + '</span>' )
				  .addTo( map );
			});
		},
		error : function(xhr,errmsg,err) {
			console.log(xhr.status + ": " + xhr.responseText);
		}
	});
};

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}
