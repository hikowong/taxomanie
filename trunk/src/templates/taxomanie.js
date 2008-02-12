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
    else {
        alert("Votre navigateur ne supporte pas les objets XMLHTTPRequest..."); 
        xhr = false; 
    } 
    return xhr
}

/**
* Methode qui sera appelee au survol d'un nom
*/
function go(taxon){
    var xhr = getXhr()
    // On defini ce qu'on va faire quand on aura la reponse
    xhr.onreadystatechange = function(){
        // On ne fait quelque chose que si on a tout recu et que le serveur est ok
        if(xhr.readyState == 4 && xhr.status == 200){
            afficheDescURL(xhr.responseText);
        }
    }
    xhr.open("GET","getImgUrl?taxon='"+taxon+"'",true);
    xhr.send(null);
}
function afficheDescURL(toThis){
    if (document.getElementById){
        document.getElementById('preview').innerHTML = toThis;
    }
    else if (document.all){
        document.all['preview'].innerHTML = toThis;
    }
}
