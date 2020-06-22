$format_search =  [
    /\[b\](.*?)\[\/b\]/ig,
    /\[i\](.*?)\[\/i\]/ig,
    /\[u\](.*?)\[\/u\]/ig,
    /\[s\](.*?)\[\/s\]/ig,
    /\[spoiler\](.*?)\[\/spoiler\]/ig,
	/^(?:(?!\<br ))([^\w>]|^)(>(?!>\d)(.+))/ig,
	/( |^|\s| |\/>)>>(\d+)( |\s|$|>|<)/mg,
	/(http|ftp|https):\/\/(?!\S+youtube\.com)([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])?/ig,
	/(http|ftp|https):\/\/(www\.)?(m\.)?(youtube\.com)\/(watch\?v=)(\S+)?/ig,
	/:upkot:/g,
	/:downkot:/g,
	/:opinion:/g,
	/'''(.+)'''/ig,
	/''(.+)''/ig,
	/__(.+)__/ig,
	/~~(.+)~~/ig,
	/\*\*(.+)\*\*/ig,
	/:waifu:/g,
	/:pepemad:/g,
	/:pardon:/g,
	/\[(color|c)=#?([0-9a-f]{3}|[0-9a-f]{6})\](.+)(\[\/(color|c)\])?/gi
];
$format_replace = [
    '<strong>$1</strong>',
    '<em>$1</em>',
	'<underline>$1</underline>',
	'<strike>$1</strike>',
	'<spoiler>$1</spoiler>',
	'<citation>&gt;$3</citation>',
	'$1<a href="#$2" class="reply">&gt;&gt;$2</a>$3',
	'<a href="$1://$2$3" class="outlink" target="_blank">$1://$2$3</a>',
	'<a class="youtube" href="$1://$2$3$4/$5$6">$1://$2$3$4/$5$6</a><span class="embed" data-url="$6">(embed)</span>',
	'<img class="sticker" src="/static/icons/upkot.png"/>',
	'<img class="sticker" src="/static/icons/downkot.png"/>',
	'<img class="sticker" src="/static/icons/neutralkot.png"/>',
    '<strong>$1</strong>',
    '<em>$1</em>',
	'<underline>$1</underline>',
	'<strike>$1</strike>',
	'<spoiler>$1</spoiler>',
	'<img class="sticker" src="/static/icons/waifu.png"/>',
	'<img class="sticker" src="/static/icons/pepe_mad.png"/>',
	'<img class="sticker" src="/static/icons/pardon.gif"/>',
	'<span style="color:#$2;">$3</span>',
];
$(document).ready(function() {
	/*$('.flag').each(function(){
		let ny = $('<img>');
		ny.attr('src','/static/icons/newyear.png');
		ny.addClass('flag-newyear');
		$(this).after(ny);
	});*/
	$('.text').each(function(){
		if (!$(this).hasClass('rendered')) {
			var txt = $(this).text();
			txt = replaceText(txt);
			$(this).html(txt);
			$(this).addClass('rendered');
		}
	});
	$('#bb-b, #bb-i, #bb-u, #bb-s, #bb-sp, #bb-c').on('click', function(e) {
		e.preventDefault();
	})
	$('#bb-c').on('click', function(e) {
		var sel = window.getSelection().toString();
		var ta = $('#text-area');
		if (ta.text() != '') {
			ta.text(ta.text() + '\n>' + sel + '\n');
		} else {
			ta.text('>' + sel + '\n');
		};
	});
	$('body').on('click', '.embed', function(e){
		e.stopPropagation();
		if ($(this).next().is('iframe')) {
			$(this).next().remove();
			$(this).text('(embed)');			 
		} else {
			let url = $(this).attr('data-url')
			let iframe = '<iframe width="480" height="320" src="https://www.youtube.com/embed/'+url+'?autoplay=1" class="youtube-frame"></iframe>';
			$(this).after(iframe);
			$(this).text('(unembed)');
		}
	})
});

function wrapText(openTag) {
    var textArea = $('#text-area');
    var closeTag = '[/'+openTag+']';
    var openTag = '['+openTag+']';
    if (typeof(textArea[0].selectionStart) != "undefined") {
        var begin = textArea.val().substr(0, textArea[0].selectionStart);
        var selection = textArea.val().substr(textArea[0].selectionStart, textArea[0].selectionEnd - textArea[0].selectionStart);
        var end = textArea.val().substr(textArea[0].selectionEnd);
        var position = begin.length + openTag.length;
        if (position < 0){ position = position * -1;}
        if (selection === "") {
			textArea.val(begin + openTag + selection + closeTag + end);
			textArea.focus();
			textArea[0].setSelectionRange(position, position);
        } else {
			textArea.val(begin + openTag + selection + closeTag + end);
			textArea.focus();
			var position = begin.length + openTag.length + selection.length;
			textArea[0].setSelectionRange(position, position);
        }
    } else {
	}
    return false;
}

function replaceText(txt) {	
	txt_split = txt.split(/\r?\n/);
	for (var j=0;j<txt_split.length;j++){
		for (var i=0;i<$format_search.length;i++) {
			txt_split[j] = txt_split[j].replace($format_search[i], $format_replace[i]);
		}
	}
	txt = txt_split.join('\n');
	return txt;
}
