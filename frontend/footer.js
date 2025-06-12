// frontend/footer.js
(function(){
  const style = document.createElement('style');
  style.innerHTML = `
    .site-footer {
      text-align: center;
      color: #7c8ead;
      font-size: 1em;
      margin: 40px 0 10px 0;
      padding-bottom: 12px;
      letter-spacing: 0.02em;
    }
    .site-footer a { color: #3f91e5; text-decoration: underline; }
    .site-footer a:hover { color: #214177; }
  `;
  document.head.appendChild(style);

  const footer = document.createElement('footer');
  footer.className = 'site-footer';
  footer.innerHTML = `
    &copy; 2025 Conception : Eric pour le Lycée Camille-Jullian, Bordeaux.<br>
    Tous droits réservés. &nbsp;|&nbsp; 
    Contact : <a href="mailto:intertech.caju@gmail.com">intertech.caju@gmail.com</a>
    <br><br>
  `;
  const mainWrap = document.querySelector('.main-wrap');
  if(mainWrap) {
    mainWrap.insertAdjacentElement('afterend', footer);
  } else {
    document.body.appendChild(footer);
  }
})();
