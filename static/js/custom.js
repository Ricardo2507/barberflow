document.body.addEventListener("change", function (evento) {
    if (evento.target.name === "hora_inicio") {
        const campoOculto = document.querySelector(
            'input[type="hidden"][name="hora_inicio"]'
        );

        if (campoOculto) {
            campoOculto.value = evento.target.value;
        }
    }
});