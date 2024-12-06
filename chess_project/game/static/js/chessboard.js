(function() {
const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
console.log('gameId:', gameId);
const socket = new WebSocket(`${wsScheme}://${window.location.host}/ws/game/${gameId}/`);

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.action === 'move') {
        updateBoard(data.fen);
        updateTurn(data);

        if (data.game_status && data.game_status !== 'active') {
            alert(data.game_status); 
            window.location.href = '/'; 
        }

    } else if (data.action === 'error') {
        alert(data.message); 
    } else if (data.action === 'exit') {
        alert('Your opponent has exited the game.');
        window.location.href = '/';
    } else if (data.action === 'game_status') {
        alert(data.message);
        window.location.href = '/';
    }
};

socket.onclose = function() {
    console.error("WebSocket connection closed unexpectedly.");
    alert("WebSocket connection lost. Please refresh the page manually.");
};

function sendMove(move) {
    if (socket.readyState === WebSocket.OPEN) {
        const payload = {
            action: 'move',
            move: move,
        };
        socket.send(JSON.stringify(payload));
    } else {
        alert('WebSocket connection is not open. Please refresh the page.');
    }
}

function movePiece() {
    const move = document.getElementById('move-input').value.toLowerCase();
    if (/^[a-h][1-8][a-h][1-8][qrbn]?$/.test(move)) { 
        sendMove(move);
    } else {
        alert('Invalid move format. Please use the UCI format (e.g., e2e4).');
    }
}

function updateBoard(fen) {
    const board = parseFEN(fen);

    for (const [square, piece] of Object.entries(board)) {
        const squareElement = document.getElementById(square);
        if (squareElement) {
            squareElement.innerHTML = piece ? piece : '&nbsp;';
        }
    }
}

function updateTurn(response) {
    const gameStatus = response.game_status || "";
    const currentTurnUsername = response.current_turn_username || "unkown";

    if (gameStatus.includes('Checkmate') || gameStatus.includes('Stalemate')) {
        document.getElementById('current-turn').textContent = gameStatus;
    } else {
        document.getElementById('current-turn').textContent = `Current Turn: ${currentTurnUsername}`;
    }
}

function parseFEN(fen) {
    const board = {};
    const rows = fen.split(' ')[0].split('/');
    const pieces = {
        'r': '&#9820;', 'n': '&#9822;', 'b': '&#9821;', 'q': '&#9819;', 'k': '&#9818;', 'p': '&#9823;',
        'R': '&#9814;', 'N': '&#9816;', 'B': '&#9815;', 'Q': '&#9813;', 'K': '&#9812;', 'P': '&#9817;'
    };

    let rank = 8;
    for (let row of rows) {
        let file = 'a';
        for (let char of row) {
            if (!isNaN(char)) {
                const emptyCount = parseInt(char);
                for (let i = 0; i < emptyCount; i++) {
                    board[`${file}${rank}`] = null;
                    file = String.fromCharCode(file.charCodeAt(0) + 1);
                }
            } else {
                board[`${file}${rank}`] = pieces[char];
                file = String.fromCharCode(file.charCodeAt(0) + 1);
            }
        }
        rank--;
    }
    return board;
}

function exitGame() {
    if (socket.readyState === WebSocket.OPEN) {
        const payload = {
            action: 'exit',
        };
        socket.send(JSON.stringify(payload));
    } else {
        alert('WebSocket connection is already closed.');
    }
}

function resetBoard() {
    window.location.reload();  
}


document.getElementById('moveBtn').addEventListener('click', movePiece);
document.getElementById('exitBtn').addEventListener('click', exitGame);

})();