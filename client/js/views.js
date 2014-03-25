
function switchToView(view) {
    view.on("deactivate", function(oldActiveItem, container, newActiveItem, eOpts) {
        if (oldActiveItem) {
            Ext.Viewport.remove(oldActiveItem, true);
        }
    });
    view.setHideAnimation('slideOut');
    view.setShowAnimation('slide');
    Ext.Viewport.setActiveItem(view);

}

///////////////////////////////////////////////////////////////////////////////
//
// 主页面
//
///////////////////////////////////////////////////////////////////////////////
Ext.define('MyApp.view.Main', {
    extend: 'Ext.Container',

    config:{
        fullscreen: true,
        baseCls: 'main-page',
        layout: {
            type: 'vbox',
            align: 'center'
        },
        items:[
            {
                xtype: 'button',
                margin: '3em 0em 0em 0em',
                baseCls: 'start-share-button',
                listeners: {
                    tap: function(){
                        switchToView(Ext.create('MyApp.view.Contract'));
                    }
                }
            },
            {
                xtype : 'container',
                docked: 'bottom',
                layout: 'hbox',
                baseCls: 'home-toolbar',
                items: [
                    {
                        xtype: 'button',
                        flex: 1,
                        text: '分享记录',
                        height: '4em',
                        icon: './images/share_list.png',
                        baseCls: 'home-share',
                        labelCls: 'home-share-label',
                        listeners: {
                            tap: function(){
                                switchToView(Ext.create('MyApp.view.VideoList'));
                            }
                        },
                    },
                    {
                        xtype: 'button',
                        flex: 1,
                        text: '我的账户',
                        height: '4em',
                        icon: './images/profile.png',
                        baseCls: 'home-profile',
                        labelCls: 'home-profile-label',
                        listeners: {
                            tap: function(){
                                Ext.Msg.alert("you!");
                            }
                        },
                    },                    
                ]
            },
        ]
    }
});


///////////////////////////////////////////////////////////////////////////////
//
// 登录，验证短信息界面
//
///////////////////////////////////////////////////////////////////////////////
Ext.define('MyApp.view.Login', {
    extend: 'Ext.Container',

    config: {
        fullscreen: true,
        layout: {
            type: 'vbox',
            align: 'center'
        },
        items: [
            {
                xtype: 'label',
                html: '输入验证码',
                margin: '2em 0em 0.5em 0em',
                style: 'font-size:1.5em;'
            },
            {
                xtype: 'textfield',
                id: 'validateNumber',
                placeHolder: '短信验证码',
                width: '12em',
                required: true,
                inputCls: 'center',
                margin: 5,
            },
            {
                xtype: 'label',
                html: '将会给您的手机下发验证码',
                style: 'font-size:0.75em;',
                margin: 5,
            },
            {
                xtype: 'button',
                width: '5em',
                margin: '3em 0em 0em 0em',
                baseCls: 'next-button',
                listeners: {
                    tap: function(){
                        // 登录
                        api_login(Ext.getCmp('mobileNumber').getValue(), 'WebClient', Ext.getCmp('validateNumber').getValue(), {
                            success: function(response){
                                // 掉转到输入验证码页面
                                data = JSON.parse(response.responseText);
                                console.log(data);
                                window.localStorage.setItem('userKey',data.UserKey);
                                window.localStorage.setItem('userKeyValidityDate',data.ValidityDate);
                                switchToView(Ext.create('MyApp.view.Main'));
                            },
                            failure: function(response, opts) {
                                Ext.Msg.alert('验证码输入错误，请确认后重新输入！');
                                console.log(response);
                            }
                        });
                    }
                }
            }
        ]
    }
});

///////////////////////////////////////////////////////////////////////////////
//
// 输入手机号界面，启动界面
//
///////////////////////////////////////////////////////////////////////////////
Ext.define('MyApp.view.Start', {
    extend: 'Ext.NavigationView',

    config: {
        id: 'MyApp.view.Start',
        fullscreen: true,
        defaultBackButtonText: '返回',
        items: [{
            xtype: 'container',
            title: '视频分享',
            layout: {
                type: 'vbox',
                align: 'center'
            },
            items: [
                {
                    xtype: 'label',
                    html: '您的手机号码',
                    margin: '2em 0em 0.5em 0em',
                    style: 'font-size:1.5em;'
                },
                {
                    xtype: 'textfield',
                    id: 'mobileNumber',
                    placeHolder: '手机号码',
                    width: '12em',
                    required: true,
                    inputCls: 'center',
                    style: 'text-align:center;',
                    margin: 5,
                },
                {
                    xtype: 'label',
                    html: '将会给您的手机下发验证码',
                    style: 'font-size:0.75em;',
                    margin: 5,
                },
                {
                    xtype: 'button',
                    width: '5em',
                    margin: '3em 0em 0em 0em',
                    baseCls: 'next-button',
                    handler: function(){
                        // 发送验证码
                        api_validate(Ext.getCmp('mobileNumber').getValue(), 'WebClient', {
                            success: function(response){
                                // 掉转到输入验证码页面
                                Ext.getCmp('MyApp.view.Start').push(Ext.create('MyApp.view.Login'));
                            },
                            failure: function(response, opts) {
                                Ext.Msg.alert('获取验证码失败，请稍后重试！');
                            }
                        });
                    }
                }
            ]
        }]
    }
});




///////////////////////////////////////////////////////////////////////////////
//
// 联系人页面
//
///////////////////////////////////////////////////////////////////////////////

var selectedContractList = new HashMap();


Ext.define('ContractItem', {
    extend: 'Ext.Container',
    config: {
        cls: 'contract-list-item',
        tpl: '<span class="image"></span><b class="checkbox"></b><span class="name">{name}</span><span class="mobile">{mobile}（{type}）</span>',
        listeners: {
            tap: function(obj){
                obj.check(!obj.isChecked());
            }
        }
    },
    _checked: false,
    isChecked: function() { return this._checked; },
    check: function(checked) {
        this._checked = checked;
        this.setCls( checked ? 'contract-list-item-checked' : 'contract-list-item' );

        this.fireAction( checked ? 'checked' : 'unchecked', [this]);

        return this._checked;
    },
    initialize: function() {
        this.callParent();
        this.element.on({
            scope      : this,
            tap        : 'onTap',
        });
    },
    onTap: function(e) {
        if (this.getDisabled()) {
            return false;
        }

        this.fireAction('tap', [this, e]);
    },    
});


Ext.define('ContractOrderItem', {
    extend: 'Ext.Container',
    config: {
        cls: 'contract-order-item',
    },
    xanchor: null,
    initialize: function() {
        this.callParent();
        this.element.on({
            scope      : this,
            tap        : 'onTap',
        });
    },
    onTap: function(e) {
        if (this.getDisabled()) {
            return false;
        }

        this.fireAction('tap', [this, e]);
    },    
});






Ext.define('MyApp.view.Contract', {
    extend: 'Ext.Container',

    config:{
        fullscreen: true,
        id: 'ContractList',
        layout: 'vbox',
        cls: 'contract-page',
        scrollable: {
            direction: 'vertical',
            directionLock: true
        },
        listeners: {
            changed: function() {
                console.log(selectedContractList.size());
                switch (selectedContractList.size()) {
                    case 0:
                        Ext.getCmp('contract-titlebar').setTitle('分享给...');
                        break;
                    case 1:
                        Ext.getCmp('contract-titlebar').setTitle('分享给'+selectedContractList.values()[1].name);
                        break;
                    default:
                        Ext.getCmp('contract-titlebar').setTitle('分享给' + selectedContractList.values()[1].name + '等' + selectedContractList.size() + '人');
                        break;
                }
            }
        },
        items:[
            {
                xtype: 'titlebar',
                id: 'contract-titlebar',
                docked: 'top',
                title: '分享给...',
                items: [
                    {
                        xtype: 'button',
                        text: '返回',
                        ui: 'back',
                        handler: function() {
                            // back main view
                            switchToView(Ext.create('MyApp.view.Main'));
                        }
                    },
                    {
                        xtype: 'button',
                        text: '分享',
                        align: 'right',
                        handler: function() {
                            // back main view
                            switchToView(Ext.create('MyApp.view.Main'));
                        }
                    }
                ]
            },
            {
                xtype: 'container',
                id: 'ContractOrderList',
                docked: 'left',
                width: '3em',
                scrollable: {
                    direction: 'vertical',
                    directionLock: true,
                    indicators: false
                }
            },
            {
                xtype: 'container',
                cls: 'contract-list',
                listeners: {
                    initialize: function(obj) {
                        var items = [
                                {
                                    order: '常用',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '移动'
                                },
                                {
                                    order: '常用',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: '常用',
                                    name: '宝宝',
                                    mobile: '18636636365',
                                    type: '联通'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'B',
                                    name: '爸爸',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                                {
                                    order: 'Z',
                                    name: 'ZZZZZ',
                                    mobile: '18636636365',
                                    type: '电信'
                                },
                            ];

                        pervOrder = '';
                        for(i=0; i<items.length; i++) {
                            item = Ext.create('ContractItem', {
                                data: items[i],
                                listeners: {
                                    checked: function(obj){
                                        c = obj.getData();
                                        if (!selectedContractList.containsKey(c.mobile)) {
                                            selectedContractList.put(c.mobile, c);
                                            Ext.getCmp('ContractList').fireAction('changed');
                                        }
                                    },
                                    unchecked: function(obj){
                                        c = obj.getData();
                                        if (selectedContractList.containsKey(c.mobile)) {
                                            selectedContractList.remove(c.mobile);
                                            Ext.getCmp('ContractList').fireAction('changed');
                                        }                                        
                                    }
                                }
                            });
                            obj.add(item);

                            // add order
                            if (pervOrder != items[i].order){
                                orderList = Ext.getCmp('ContractOrderList');
                                orderItem = Ext.create('ContractOrderItem', {
                                    html: items[i].order,
                                    listeners: {
                                        tap: function(orderItem) {
                                            orderItem.xanchor.element.dom.scrollIntoView(true);
                                        }
                                    }
                                });
                                orderItem.xanchor = item;
                                orderList.add(orderItem);
                                pervOrder = items[i].order;
                            }
                        }
                    }
                }
            }
        ],
    }
});






///////////////////////////////////////////////////////////////////////////////
//
// 分享时间轴
//
///////////////////////////////////////////////////////////////////////////////
Ext.define('MyApp.view.VideoList', {
    extend: 'Ext.Container',

    config: {
        id: 'MyApp.view.VideoList',
        fullscreen: true,
        cls: 'videolist-page',
        scrollable: {
            direction: 'vertical',
            directionLock: true
        },
        listeners: {
            initialize: function() {
                this.add(Ext.create('My.VideoList', {id: 'video-list'}));
            }
        },
        items: [
            {
                xtype: 'titlebar',
                id: 'contract-titlebar',
                docked: 'top',
                title: '分享记录',
                items: [
                    {
                        xtype: 'button',
                        text: '返回',
                        ui: 'back',
                        handler: function() {
                            // back main view
                            switchToView(Ext.create('MyApp.view.Main'));
                        }
                    },
                ]
            },
        ]
    }
});


Ext.define('My.VideoList', {
    extend: 'Ext.Container',

    config: {
        id: 'video-list',
        cls: 'video-list',
    },

    _offset: 0,
    _max: 10,
    initialize: function() {
        api_list_sharevideo(window.localStorage.getItem('userKey'), this._offset, this._max, {
                success: function(response){
                    // 掉转到输入验证码页面
                    data = JSON.parse(response.responseText);
                    console.log(data);
                    for( i = 0; i < data.Results.length; i++) {
                        video = Ext.create('My.VideoListItem', {
                            data: {VID: data.Results[i].VID, Duration: data.Results[i].Duration, url: data.Results[i].VideoURLs[0], poster: data.Results[i].PosterURLs[0]},
                            listeners: {
                            }
                        });
                        Ext.getCmp('video-list').add(video);
                    }
                },
                failure: function(response, opts) {
                    Ext.Msg.alert('获取数据失败，请稍后重试！');
                    console.log(response);
                }
            });
    },

});


Ext.define('My.VideoListItem', {
    extend: 'Ext.Container',
    config: {
        cls: 'video-list-item',
        tpl: '<span>{Duration}</span><video src="{url}" poster="{poster}" controls="controls"></video>',
        listeners: {
            tap: function(obj){
            }
        }
    },

    initialize: function() {
        this.callParent();
        this.element.on({
            scope      : this,
            tap        : 'onTap',
        });
    },

    onTap: function(e) {
        if (this.getDisabled()) {
            return false;
        }

        this.fireAction('tap', [this, e]);
    },    
});

