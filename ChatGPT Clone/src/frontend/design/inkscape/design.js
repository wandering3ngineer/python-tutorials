// Set the document height and width to 100%
document.documentElement.setAttribute("height", "100%");
document.documentElement.setAttribute("width", "100%");

// Initially only show layer one
document.addEventListener("DOMContentLoaded", function() {
    showLayer('layer1');
});

// Shows or hides a layer with a given id
function showLayer(id) 
{
 const layers = document.querySelectorAll("svg > g[*|groupmode=layer]");
 layers.forEach(layer => {
          layer.style.display = "none"
 });

 const layerToShow = document.querySelector("#" + id);
 layerToShow.style.display = "inline";
}