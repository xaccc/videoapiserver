//
// 主页面
//
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
                        Ext.Viewport.setActiveItem(Ext.create('MyApp.view.Contract'));
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
                                Ext.Msg.alert("Fuck!");
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


//
// 登录，验证短信息界面
//
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
                                Ext.Viewport.setActiveItem(Ext.create('MyApp.view.Main'));
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

//
// 输入手机号界面，启动界面
//
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

var selectedContractList = new HashMap();

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
                            Ext.Viewport.setActiveItem(Ext.create('MyApp.view.Main'));
                        }
                    },
                    {
                        xtype: 'button',
                        text: '分享',
                        align: 'right',
                        handler: function() {
                            // back main view
                            Ext.Viewport.setActiveItem(Ext.create('MyApp.view.Main'));
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
