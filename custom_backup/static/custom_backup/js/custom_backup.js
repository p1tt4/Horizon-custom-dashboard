/* Additional JavaScript for custom_backup. */
'use strict';

let BACKUP_TYPE_DEFAULT = 'auto';
let MAX_BACKUP_DEFAULT_VALUE = '0';
let MAX_SNAPSHOT_DEFAULT_VALUE = '0';


class FieldWrapper {
    constructor(id) {
        this._elem = document.getElementById(id);
        if (this._elem === null){
            throw "Element with ID: " + id + " not found in the DOM";
        }

    }
    get elem() {
        return this._elem;
    }
    get val() {
        return this._elem.value;
    }
    set onclick(callback) {
        this._elem.onclick = callback;
    }
    get isVisible() {
        return ! this._elem.classList.contains('hidden-elem');
    }
}

FieldWrapper.prototype.hasClass = function(className) {
    this._elem.classList.contains(className);
}
FieldWrapper.prototype.show = function() {
    this._elem.classList.remove('hidden-elem');
}
FieldWrapper.prototype.hide = function() {
    this._elem.classList.add('hidden-elem');
}
FieldWrapper.prototype.resetSelect = function(val) {
    let defaultValue = (val !== undefined) ? val : "";
    for (let _select of this._elem.getElementsByTagName('select')) {
        _select.value = defaultValue;
    }
}
FieldWrapper.prototype.resetInput = function(val) {
    let defaultValue = (val !== undefined) ? val : "";
    for (let _input of this._elem.getElementsByTagName('input')) {
        _input.value = defaultValue;
    }
}

// TODO to rename
function InputHandler() {
    let metadataBtn = new FieldWrapper('metadata-btn');
    let metadataRow = new FieldWrapper('metadata-row');
    let instanceBtn = new FieldWrapper('instance-btn');
    let instanceRow = new FieldWrapper('instance-row');

    metadataBtn.onclick = function(){
        if (metadataRow.isVisible) return;
        metadataRow.show()
        instanceRow.hide();
//        instanceRow.resetSelect(); TODO: to verify. Temporary disabled
    }
    instanceBtn.onclick = function(){
        if (instanceRow.isVisible) return;
        instanceRow.show();
        metadataRow.hide();
//        TODO: is it correct to reset the input after hiding the element
//        metadataRow.resetInput();
    }

    let backupCollapse = new FieldWrapper("backup-collapse");
    let snapshotCollapse = new FieldWrapper("snapshot-collapse");
    let snapshotMode = document.getElementById('snapshot-mode-btn');
    let backupMode = document.getElementById('backup-mode-btn');
    snapshotMode.onclick = function(e) {
        if (! snapshotCollapse.isVisible) {
            backupCollapse.hide();
            snapshotCollapse.show();
//            backupCollapse.resetInput(MAX_BACKUP_DEFAULT_VALUE);
//            backupCollapse.resetSelect(BACKUP_TYPE_DEFAULT);
        }
    };
    backupMode.onclick = function(e) {
        if (! backupCollapse.isVisible) {
            snapshotCollapse.hide();
            backupCollapse.show();
//            snapshotCollapse.resetInput(MAX_SNAPSHOT_DEFAULT_VALUE)
        }
    };

    let modalWrapper = document.getElementById("modal_wrapper");
    let finalBtn = document.getElementsByClassName('button-final')[0]
    finalBtn.onclick = function(e) {
        if (modalWrapper.getElementsByTagName('form').length === 0){
            console.log("Error: no Form found");
            return false;
        }
        modalWrapper.getElementsByTagName('form')[0].submit();
        return false;
    };
}


document.getElementById('jobs__action_create').onclick = function (e){
    setTimeout(InputHandler, 1500);
}


let updateButtons = document.getElementsByClassName('btn data-table-action btn-default btn-sm ajax-modal');
for (let updateBtn of updateButtons){
    if (updateBtn.id !== "" && updateBtn.id.indexOf('action_update') > -1) {
        updateBtn.onclick = function (e){
            setTimeout(InputHandler, 1500);
        }
    }
}
