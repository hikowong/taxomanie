
/**
* Please wait on submit
**/
$(document).ready(function() { 
    $('#send').click(function() { 
        $.blockUI(); 
    }); 
}); 

/**
* Images
**/
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
            afficheDescURL(taxon,xhr.responseText);
        }
    }
    xhr.open("GET","getImgUrl?taxon="+taxon,true);
    xhr.send(null);
}
function afficheDescURL(taxon,toThis){
    if(taxon!=''){
    if (document.getElementById){
        document.getElementById('preview').innerHTML = "<div class='nameTaxa'>"+taxon+"</div>"+toThis;
    }
    else if (document.all){
        document.all['preview'].innerHTML = "<div class='nameTaxa'>"+taxon+"</div>"+toThis;
    }
    }
}

/*
 * show/hide intern node
 */
function setNode(){
    $(document).ready(function(){
         $("a.genre").toggle();
         $("a.showparents").toggle();
    });
}

/*
 * Develop/hide intern node
 */
$(document).ready(function(){
    $("div.interparents").hide();
});

function setInternNode(idNode){
    $(document).ready(function(){
         $("#"+idNode).slideToggle(500,function () {
             if ($("#a-"+idNode).text() == "hide" ){
                 $("#a-"+idNode).attr( "style", "color:grey" );
                 $("#a-"+idNode).text("show parents");
             }
             else{
                 $("#a-"+idNode).text("hide");
                 $("#a-"+idNode).attr( "style", "color:red" );
             }
           });
    });
}

function toggleInternNode(){
    $(document).ready(function(){
         $("div.interparents").slideToggle(60);
         if ("hide" in $("a.showparents").text() ){
             $("a.showparents").attr("style", "color:grey" );
             $("a.showparents").text("show parents");
         }
         else{
             $("a.showparents").attr("style", "color:red" );
             $("a.showparents").text("hide");
         }
    });
}


