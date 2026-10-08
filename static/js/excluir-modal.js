// Preenche o modal de confirmação com os dados do item a ser excluído
// (cliente, produto etc.). O botão "Excluir" da linha informa nome e URL.
document.addEventListener("DOMContentLoaded", function () {
    var modal = document.getElementById("modalExcluir");
    if (!modal) return;

    modal.addEventListener("show.bs.modal", function (evento) {
        var botao = evento.relatedTarget;
        document.getElementById("nomeItemExcluir").textContent = botao.dataset.nome;
        document.getElementById("formExcluir").action = botao.dataset.action;
    });
});
