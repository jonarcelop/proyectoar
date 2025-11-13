function $(id) {
    return document.getElementById(id);
}

function log(msg) {
    const logEl = $("log");
    logEl.innerHTML += msg + "<br>";
    logEl.scrollTop = logEl.scrollHeight;
}

function renderBoard(board, clickHandler) {
    const boardEl = $("board");
    boardEl.innerHTML = "";

    board.forEach((row, r) => {
        row.forEach((cell, c) => {
            const div = document.createElement("div");
            div.className = "cell";
            div.innerText = cell === "-" ? "" : cell;
            div.onclick = () => clickHandler(r, c);
            boardEl.appendChild(div);
        });
    });
}

function blockBoard() {
    document.querySelectorAll(".cell").forEach(c => c.classList.add("disabled"));
}

function unblockBoard() {
    document.querySelectorAll(".cell").forEach(c => c.classList.remove("disabled"));
}
