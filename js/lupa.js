// Lupa: abre as imagens em grande dentro da página, com setas para a anterior e a seguinte.
// Sem JavaScript, cada miniatura continua a ser um link para a imagem grande.
(function () {
  const lupa = document.querySelector(".lupa");
  if (!lupa || typeof lupa.showModal !== "function") return;
  const img = lupa.querySelector("img");
  const leg = lupa.querySelector("figcaption");
  let grupo = [], i = 0;

  function mostra(k) {
    i = (k + grupo.length) % grupo.length;
    const a = grupo[i];
    img.src = a.dataset.larga;
    img.alt = a.querySelector("img").alt || "";
    const d = a.dataset.descricao ? `<span class="descricao">${a.dataset.descricao}</span>` : "";
    leg.innerHTML = (a.dataset.legenda || "") + d;
    const varias = grupo.length > 1;
    lupa.querySelector(".anterior").hidden = !varias;
    lupa.querySelector(".seguinte").hidden = !varias;
  }

  document.addEventListener("click", function (e) {
    const a = e.target.closest("a[data-larga]");
    if (!a || e.metaKey || e.ctrlKey || e.shiftKey) return;
    e.preventDefault();
    grupo = Array.from(document.querySelectorAll(`a[data-larga][data-grupo="${a.dataset.grupo}"]`));
    mostra(grupo.indexOf(a));
    lupa.showModal();
  });
  lupa.querySelector(".fechar").addEventListener("click", () => lupa.close());
  lupa.querySelector(".anterior").addEventListener("click", () => mostra(i - 1));
  lupa.querySelector(".seguinte").addEventListener("click", () => mostra(i + 1));
  lupa.addEventListener("click", (e) => { if (e.target === lupa) lupa.close(); });
  document.addEventListener("keydown", (e) => {
    if (!lupa.open) return;
    if (e.key === "ArrowLeft") mostra(i - 1);
    if (e.key === "ArrowRight") mostra(i + 1);
  });
  lupa.addEventListener("close", () => { img.removeAttribute("src"); });
})();
