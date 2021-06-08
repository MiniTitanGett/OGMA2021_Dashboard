document.getElementById('{"index":4, "type":"confirm-load-data"}').onclick = function(){
    var newDiv = document.createElement('div');
    newDiv.className = '_data-loading';
    newDiv.id = 'loading';
    document.body.appendChild(newDiv, document.getElementById('content'));
    while (document.getElementById('{"index":4, "type":"confirm-load-data"}').data-dash-is-loading) {
        /* Do Nothing */
    }
    document.getElementById('loading').remove();
}