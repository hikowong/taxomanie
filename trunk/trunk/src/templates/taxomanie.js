function getXhr(){
    var xhr = null; 
    if(window.XMLHttpRequest) // Firefox et autres
        xhr = new XMLHttpRequest(); 
    else if(window.ActiveXObject){ // Internet Explorer 
        try {
                xhr = new ActiveXObject("Msxml2.XMLHTTP");
            } catch (e) {
                xhr = new ActiveXObject("Microsoft.XMLHTTP");
            }
    }
    else { // XMLHttpRequest non supporté par le navigateur 
        alert("Votre navigateur ne supporte pas les objets XMLHTTPRequest..."); 
        xhr = false; 
    } 
    return xhr
}

/**
* Methode qui sera appelee au survol d'un nom
*/
function go(){
    var xhr = getXhr()
    // On defini ce qu'on va faire quand on aura la reponse
    xhr.onreadystatechange = function(){
        // On ne fait quelque chose que si on a tout recu et que le serveur est ok
        if(xhr.readyState == 4 && xhr.status == 200){
            afficheDescURL(xhr.responseText);
        }
    }
    xhr.open("GET","essaiAJAX.php",true);
    xhr.send(null);
}
function afficheDescURL(id, toThis){
    if (document.getElementById){
        document.getElementById(id).innerHTML = toThis;
    }
    else if (document.all){
        document.all[id].innerHTML = toThis;
    }
}
//#1234 { position:absolute; z-index:3; top:8px; right:0px; text-align:left; border-style:solid; border-width:thin; background:lightgrey;}
//<a id="le_nom_du_truc" class="genre" href="http://www.apple.com/fr" onmouseover='go()' onmouseout="afficheDescURL('','')">Pan</a>
