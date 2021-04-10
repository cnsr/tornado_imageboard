// TODO: animate
const closePopup = (element) => element.closest('.popup').remove();

function popUp(data) {
	document.querySelectorAll('.popup').forEach(el => el.remove())
	let pop = document.createElement('div');
	pop.classList.add('popup');
	pop.innerHTML = `<div id="popup-inner">${data}</div><button id="popup-close" onclick='closePopup(this);'>X</button>`;
	document.getElementsByTagName('body')[0].appendChild(pop);
}
