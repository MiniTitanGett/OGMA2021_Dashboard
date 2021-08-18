
function resizeContentWrapper() {
  try {
    heightTabs = document.getElementById("tab-menu-header").offsetHeight;
    heightMenu = document.getElementById("button-save-dashboard-wrapper").offsetHeight;
    heightTotal = document.getElementById("page-content").offsetHeight;
    document.getElementById("tab-content-wrapper").style.maxHeight = String(heightTotal - heightMenu - heightTabs) + 'px';
  }
  catch (error){ /* Do Nothing */ }
}

window.onresize = resizeContentWrapper;

// helper addition to arrays to allow for easy comparisons
// https://stackoverflow.com/questions/7837456/how-to-compare-arrays-in-javascript

// Warn if overriding existing method
if(Array.prototype.equals)
    console.warn("Overriding existing Array.prototype.equals. Possible causes: New API defines the method, there's a framework conflict or you've got double inclusions in your code.");
// attach the .equals method to Array's prototype to call it on any array
Array.prototype.equals = function (array) {
    // if the other array is a falsy value, return
    if (!array)
        return false;

    // compare lengths - can save a lot of time
    if (this.length != array.length)
        return false;

    for (let i = 0, l = this.length; i < l; i++) {
        // Check if we have nested arrays
        if (this[i] instanceof Array && array[i] instanceof Array) {
            // recurse into the nested arrays
            if (!this[i].equals(array[i]))
                return false;
        }
        else if (this[i] != array[i]) {
            // Warning - two different object instances will never be equal: {x:20} != {x:20}
            return false;
        }
    }
    return true;
}

// Hide method from for-in loops
Object.defineProperty(Array.prototype, "equals", {enumerable: false});

// helper function used by clientside callbacks to compare objects
function isEquivalent(a, b) {
    // Create arrays of property names
    let aProps = Object.getOwnPropertyNames(a);
    let bProps = Object.getOwnPropertyNames(b);

    // If number of properties is different,
    // objects are not equivalent
    if (aProps.length != bProps.length) {
        return false;
    }

    for (let i = 0; i < aProps.length; i++) {
        let propName = aProps[i];

        // If values of same property are not equal,
        // objects are not equivalent
        if (a[propName] !== b[propName]) {
            return false;
        }
    }

    // If we made it this far, objects
    // are considered equivalent
    return true;
}


// Handles Resizing of ContentWrapper, uses x as a throw away output, takes x,y,z and throw away inputs to trigger when tabs are modified
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        resizeContentWrapper: function(x,y,z) {
            resizeContentWrapper();
            return x
        },
        graphLoadScreen0: function(trigger) {
            if (trigger == 'confirm-load'){
                let newDiv = document.createElement('div');
                newDiv.className = '_graph-data-loading';
                newDiv.id = 'graph-loading0';
                document.getElementById('{"index":0,"type":"tile-view-content"}').appendChild(newDiv);
            }
            return 0;
        },
        graphRemoveLoadScreen0: function(data, num_tiles) {
            try{
                document.getElementById('graph-loading0').remove();
            }catch(error){ /* Do Nothing */ }
            return 0;
        },
        graphLoadScreen1: function(trigger) {
            if (trigger == 'confirm-load'){
                let newDiv = document.createElement('div');
                newDiv.className = '_graph-data-loading';
                newDiv.id = 'graph-loading1';
                document.getElementById('{"index":1,"type":"tile-view-content"}').appendChild(newDiv);
            }
            return 0;
        },
        graphRemoveLoadScreen1: function(data, num_tiles) {
            try{
                document.getElementById('graph-loading1').remove();
            }catch(error){ /* Do Nothing */ }
            return 0;
        },
        graphLoadScreen2: function(trigger) {
            if (trigger == 'confirm-load'){
                let newDiv = document.createElement('div');
                newDiv.className = '_graph-data-loading';
                newDiv.id = 'graph-loading2';
                document.getElementById('{"index":2,"type":"tile-view-content"}').appendChild(newDiv);
            }
            return 0;
        },
        graphRemoveLoadScreen2: function(data, num_tiles) {
            try{
                document.getElementById('graph-loading2').remove();
            }catch(error){ /* Do Nothing */ }
            return 0;
        },
        graphLoadScreen3: function(trigger) {
            if (trigger == 'confirm-load'){
                let newDiv = document.createElement('div');
                newDiv.className = '_graph-data-loading';
                newDiv.id = 'graph-loading3';
                document.getElementById('{"index":3,"type":"tile-view-content"}').appendChild(newDiv);
            }
            return 0;
        },
        graphRemoveLoadScreen3: function(data, num_tiles) {
            try{
                document.getElementById('graph-loading3').remove();
            }catch(error){ /* Do Nothing */ }
            return 0;
        }
    }
});


