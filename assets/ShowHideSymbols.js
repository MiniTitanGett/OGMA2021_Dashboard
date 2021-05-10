
function showHideSaveSymbols (container, button) {

  if (!container.is(event.target) && !container.has(event.target).length &&
      !button.is(event.target) && !button.has(event.target).length &&
      $(container).is(':visible')) {
      container.hide();
  }

  if (button.is(event.target) || button.has(event.target).length && !$(container).is(':visible')) {
    container.show();
  }
}


function showHideResetSymbols (container, button) {
  if (!button.is(event.target) && !button.has(event.target).length && $(container).is(':visible')) {
      container.hide();
  }

  if (button.is(event.target) || button.has(event.target).length && !$(container).is(':visible')) {
    container.show();
  }
}


// if overwriting controls are visible, hide if a click is not on the overwriting controls or the 'save' button
$(document).click(function() {

  // dashboard overwrite controls
  var dashboardContainer = $("#save-status-symbols-inner");
  var dashboardButton = $("#button-save-dashboard");
  showHideSaveSymbols(dashboardContainer, dashboardButton);

  // tile overwrite controls
  var i
  for (i = 0; i < 4; i++) {
    var tileContainer = $(".save-symbols-showHide-wrapper-" + i.toString());
    var tileButton = $(".tile-save-button-" + i.toString());
    showHideSaveSymbols(tileContainer, tileButton);
  }

  // dashboard reset controls
  var dashboardResetContainer = $("#dashboard-reset-symbols");
  var dashboardResetButton = $("#dashboard-reset");
  showHideResetSymbols(dashboardResetContainer, dashboardResetButton);

});
