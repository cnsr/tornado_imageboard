var default_theme = 'themes/brutalism.css';

document.addEventListener("DOMContentLoaded", (event) => {
	var pageBottom = document.getElementById("top");
	var pageTop = document.getElementsByTagName('header')[0];

	document.getElementsByTagName('html')[0].style.scrollBehavior = 'smooth';
	document.querySelectorAll(`[value="${localStorage.theme}"]`).forEach(el => el.setAttribute('selected', true));

	document.getElementById('themes').addEventListener('change', function (e) {
		localStorage.theme = e.target.value.replace("null", default_theme);
	});

	document.getElementById('settings-btn').addEventListener('click', function (e) {
		toggleMenuDisplay()
	});

	document.getElementById('settings-hide').addEventListener('click', function (e) {
		toggleMenuDisplay()
	});

	document.getElementById('top').addEventListener("click", function() {
		pageTop.scrollIntoView()
	})

	document.getElementById('btm').addEventListener("click", function() {
		pageBottom.scrollIntoView()
	})
});

const toggleMenuDisplay = () => {
	//  this is pretty ugly but cba tbh
	let display = document.getElementById('settings-menu').style.display, newDisplay;
	if (!display | display === 'none') {newDisplay = 'block'} else newDisplay = 'none';
	document.getElementById('settings-menu').style.display = newDisplay;
}

const getTheme = () => {
	if (typeof localStorage.theme != 'undefined') {
		getCSS(localStorage.theme);
		document.querySelectorAll(`[value="${localStorage.theme}"]`).forEach(el => el.setAttribute('selected', true));
	} else {
		getCSS(default_theme);
		localStorage.theme = default_theme;		
		document.querySelectorAll(`[value="${localStorage.theme}"]`).forEach(el => el.attsetAttributer('selected', true));
	};
}

const getCSS = (file) => {
	if (!file.startsWith('themes')) file = `themes/${file}`;
	let _css = document.getElementById('_css');
    if (_css) {
        _css.remove();
    }
    let link = document.createElement('link');
    link.id = '_css';
    link.rel = 'stylesheet';
    link.type = 'text/css';
    link.href = '/static/' + file;
    link.media = 'all';
    document.getElementsByTagName('head')[0].append(link);
}
