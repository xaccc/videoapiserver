
var apiBaseURL = '/videoapiserver/api';



Ext.Ajax.setTimeout(10000);



function api_validate(mobile, device, params){
    Ext.Ajax.request(Ext.Object.merge({
        url: apiBaseURL + '/validate',
        jsonData: {
            Mobile: mobile,
            Device: device
        }
    }, params));    
}

function api_login(id, device, validate, params){
    Ext.Ajax.request(Ext.Object.merge({
        url: apiBaseURL + '/login',
        jsonData: {
            Id: id,
            Device: device,
            Validate: validate,
        }
    }, params));    
}