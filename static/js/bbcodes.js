// TODO: extract into a separate file at some point
const formatterPairs = [
	{
		regex: /\[b](.*?)\[\/b]/ig,
		result: '<strong>$1</strong>',
	},
	{
		regex: /\[i](.*?)\[\/i]/ig,
		result: '<em>$1</em>',
	},
	{
		regex: /\[u](.*?)\[\/u]/ig,
		result: '<underline>$1</underline>',
	},
	{
		regex: /\[s](.*?)\[\/s]/ig,
		result: '<s>$1</s>',
	},
	{
		regex: /\[spoiler](.*?)\[\/spoiler]/ig,
		result: '<spoiler>$1</spoiler>',
	},
	{
		regex: /^(?!<br )([^\w>]|^)(>(?!>\d)(.+))/ig,
		result: '<citation>&gt;$3</citation>',
	},
	{
		regex: /( |^|\s| |\/>)>>(\d+)( |\s|$|>|<)/mg,
		result: '$1<a href="#$2" class="reply">&gt;&gt;$2</a>$3',
	},
	{
		regex: /(http|ftp|https):\/\/(?!\S+youtube\.com)([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])?/ig,
		result: '<a href="$1://$2$3" class="outlink" target="_blank">$1://$2$3</a>',
	},
	{
		regex: /(http|ftp|https):\/\/(www\.)?(m\.)?(youtube\.com)\/(watch\?v=)(\S+)?/ig,
		result: '<a class="youtube" href="$1://$2$3$4/$5$6">$1://$2$3$4/$5$6</a><span class="embed" data-url="$6">(embed)</span>',
	},
	{
		regex: /:upkot:/g,
		result: '<img class="sticker" src="/static/icons/upkot.png" alt="Kot giving thumbsup"/>',
	},
	{
		regex: /:downkot:/g,
		result: '<img class="sticker" src="/static/icons/downkot.png" alt="Kot giving thumbsdown"/>',
	},
	{
		regex: /:opinion:/g,
		result: '<img class="sticker" src="/static/icons/neutralkot.png" alt="Kot with neutral expression"/>',
	},
	{
		regex: /'''(.+)'''/ig,
		result: '<strong>$1</strong>',
	},
	{
		regex: /''(.+)''/ig,
		result: '<em>$1</em>',
	},
	{
		regex: /__(.+)__/ig,
		result: '<underline>$1</underline>',
	},
	{
		regex: /~~(.+)~~/ig,
		result: '<strike>$1</strike>',
	},
	{
		regex: /\*\*(.+)\*\*/ig,
		result: '<spoiler>$1</spoiler>',
	},
	{
		regex: /:waifu:/g,
		result: '<img class="sticker" src="/static/icons/waifu.png" alt="Goddess"/>',
	},
	{
		regex: /:pepemad:/g,
		result: '<img class="sticker" src="/static/icons/pepe_mad.png" alt="A mad frogger"/>',
	},
	{
		regex: /:pardon:/g,
		result: '<img class="sticker" src="/static/icons/pardon.gif" alt="Very sorry"/>',
	},
	{
		regex: /\[(color|c)=#?([0-9a-f]{3}|[0-9a-f]{6})](.+?)(\[\/(color|c)])?/gi,
		result: '<span style="color:#$2;">$3</span>',
	},
]

const isCloseToNewYearsEve = () => {
	let d = new Date();
	if (d.getMonth() === 1) {
		return d.getDate() < 16;
	} else if (d.getMonth() === 11) return d.getDate() > 20;
	return false;
}

document.addEventListener('DOMContentLoaded', (e) => {
	if (isCloseToNewYearsEve()) {
		[...document.getElementsByClassName('flag')].map(el => {
			el.insertAdjacentElement(
				'afterend', '<img src="/static/icons/newyear.png" class="flag-newyear"/>'
			);
		});
	}
	[...document.getElementsByClassName('text')].map(el => {
		if (!el.classList.contains('rendered')) {
			el.innerHTML = replaceText(el.innerText);
			el.classList.add('rendered');
		}
	});
	['bb-b', 'bb-i', 'bb-u', 'bb-s', 'bb-sp', 'bb-c'].map(tagId => {
		if (document.getElementById(tagId))
			document.getElementById(tagId).addEventListener('click', e => e.preventDefault());
	})
	if (document.getElementById('bb-c')) {
		document.getElementById('bb-c').addEventListener('click', e => {
			var sel = window.getSelection().toString();
			var ta = document.getElementById('text-area');
			if (ta.innerText.length) {
				ta.innerText = ta.innerText + '\n>' + sel + '\n';
			} else {
				ta.innerText = '>' + sel + '\n';
			}
		});
	}

	[...document.getElementsByClassName('embed')].forEach(el => el.addEventListener('click', processEmbed));
});

const processEmbed = e => {
	e.stopPropagation();
	if (e.target.nextSibling && e.target.nextSibling.tagName === 'iframe') {
		e.target.nextSibling.remove()
		e.target.innerText = '(embed)';
	} else {
		let url = e.target.getAttribute('data-url')
		e.target.insertAdjacentHTML(
			'afterend',
			`<iframe width="480" height="320" src="https://www.youtube.com/embed/${url}?autoplay=1" class="youtube-frame"></iframe>`
		);
		e.target.innerText = '(unembed)';
	}
}

const wrapText = (tag) => {
    let textArea = document.getElementById('text-area');
	let openTag = `[${tag}]`;
	let closeTag = `[/${tag}]`;
	let start = textArea.selectionStart;
	let end = textArea.selectionEnd;
	// textArea .selectionStart and .selectionEnd are 0 by default
    if (start !== end) {
        let begin = textArea.value.substr(0, start);
        let selection = textArea.value.substr(start, end - start);
        let remainder = textArea.value.substr(textArea[0].selectionEnd);

        let position = begin.length + openTag.length;

        if (position < 0) position = position * -1;

        if (selection.length) {
			textArea.value = begin + openTag + selection + closeTag + remainder;
			textArea.focus();
			textArea.setSelectionRange(position, position);
        } else {
			textArea.value = begin + openTag + selection + closeTag + remainder;
			textArea.focus();
			position = begin.length + openTag.length + selection.length;
			textArea.setSelectionRange(position, position);
        }
    } else {
	}
    return false;
}

function replaceText(txt) {	
	let textSegments = txt.split(/\r?\n/);
	textSegments.map((text) => {
		formatterPairs.map((pair) => {
			text.replaceAll(pair.regex, pair.result);
		});
	})
	return textSegments.join('\n');
}
