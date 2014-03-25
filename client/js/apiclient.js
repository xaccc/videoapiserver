
var apiBaseURL = '/videoapiserver/api';


Ext.Ajax.setTimeout(10000);
Ext.Ajax.on('beforerequest', function(){        
    Ext.Viewport.setMasked({ xtype: 'loadmask', message: "加载数据..." });
});
Ext.Ajax.on('requestcomplete', function(){      
    Ext.Viewport.setMasked(false);
});
Ext.Ajax.on('requestexception', function(){
    Ext.Viewport.setMasked(false);
});


function api_validate(mobile, device, params){
    Ext.Ajax.request(Ext.Object.merge({
        method: 'POST',
        url: apiBaseURL + '/validate',
        jsonData: {
            'Mobile': mobile,
            'Device': device
        }
    }, params));    
}

function api_login(id, device, validate, params){
    Ext.Ajax.request(Ext.Object.merge({
        method: 'POST',
        url: apiBaseURL + '/login',
        jsonData: {
            'Id': id,
            'Device': device,
            'Validate': validate,
        }
    }, params));
}


function api_list_sharevideo(userKey, offset, max, params){
    Ext.Ajax.request(Ext.Object.merge({
        method: 'POST',
        url: apiBaseURL + '/listsharevideo',
        jsonData: {
            'UserKey': userKey,
            'Offset': offset,
            'Max': max,
        }
    }, params));    
}

