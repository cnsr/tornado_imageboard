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

export const replaceText = (txt) => {
	let textSegments = txt.split(/\r?\n/);
	return textSegments.map((text) => {
		formatterPairs.map((pair) => {
			if (text.search(pair.regex) !== -1) {
				text = text.replaceAll(pair.regex, pair.result);
			}
		});
		return text
	}).join('\n');
}