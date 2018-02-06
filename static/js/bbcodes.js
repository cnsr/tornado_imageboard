$format_search =  [
    /\[b\](.*?)\[\/b\]/ig,
    /\[i\](.*?)\[\/i\]/ig,
    /\[u\](.*?)\[\/u\]/ig,
    /\[s\](.*?)\[\/s\]/ig,
    /\[spoiler\](.*?)\[\/spoiler\]/ig,
	/([^\w>]|^)(>(?!>\d)(.+))/ig,
	/( |^|\s)>>(\d+)( |\s|$)/ig
];
$format_replace = [
    '<strong>$1</strong>',
    '<em>$1</em>',
	'<underline>$1</underline>',
	'<strike>$1</strike>',
	'<spoiler>$1</spoiler>',
	'<citation>&gt;$3</citation>',
	'<a href="#$2" class="reply">&gt;&gt;$2</a><br>',
];
$(document).ready(function() {
	$('.text').each(function(){
		var txt = $(this).text();
		for (var i =0;i<$format_search.length;i++) {
			txt = txt.replace($format_search[i], $format_replace[i]);
		}
		$(this).html(txt);
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
	$('#toggle').on('click', function(e){
		 e.preventDefault();
		 $('form').toggle();
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
