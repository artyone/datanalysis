from PyQt5.QtGui import QColor, QPalette


def defaultSettings(settings, appVersion):
    '''
    Функция установки стандартных настроек приложения
    '''
    settings.setValue('version', appVersion)
    settings.setValue(
        'koef_for_intervals',
        {
            # макс разница, макс значение
            'tang': [4, 10],
            # макс разница, макс значение
            'kren': [1.4, 10],
            # макс разница, макс значение
            'h': [20, 200],
            # макс отношение, макс значение,усредение до, усреднение в моменте
            'wx': [0.025, 200, 150, 50]
        }
    )
    headers = (
        'popr_prib_cor_V_cod',
        'popr_prib_cor_FI_cod',
        'popr_prib_cor_B_cod',
        'kurs_DISS_grad',
        'kren_DISS_grad',
        'tang_DISS_grad',
        'k',
        'k1'
    )
    planesParams = {
        'mdm': dict(zip(headers, (5, 14, 2, -0.62, 0.032, 3.33 - 0.032, 1, 1))),
        'm2': dict(zip(headers, (7, 6, 1, 0.2833, 0.032, 3.33 - 0.2, 1, 1))),
        'IL78m90a': dict(zip(headers, (7, 15, 1, 0.27, 0, 3.33, 1, 1))),
        'IL76md90a': dict(zip(headers, (6, 15, 1, 0 - 0.665, -0.144, 3.33, 1, 1))),
        'tu22': dict(zip(headers, (6, 6, 2, 0, 0, 0, 1 / 3.6, 0.00508))),
        'tu160': dict(zip(headers, (6, 10, 1, 0, 0, -2.5, 1, 1)))
    }
    settings.setValue('planes', planesParams)
    settings.setValue('map', {'jvdHMin': '100', 'decimation': '20'})
    settings.setValue('lastFile', None)
    corrections = {
        'koef_Wx_PNK': 1, 'koef_Wy_PNK': 1, 'koef_Wz_PNK': 1,
        'kurs_correct': 0, 'kren_correct': 0, 'tang_correct': 0
    }
    settings.setValue('corrections', corrections)
    graphs = {
        'background': 'black',
        'default': [
            {
                "name": "Анализ Wp",
                "rows": [
                        {
                            "row": 1,
                            "width": 23,
                            "fields": [
                                {
                                    "category": "PNK",
                                    "adr": "ADR8",
                                    "column": "JVD_H",
                                },
                            ]
                        },
                    {
                            "row": 2,
                            "width": 25,
                            "fields": [
                                {
                                    "category": "PNK",
                                    "adr": "ADR8",
                                    "column": "I1_Kren",
                                },
                                {
                                    "category": "PNK",
                                    "adr": "ADR8",
                                    "column": "I1_Tang",
                                }
                            ]
                        },
                    {
                            "row": 3,
                            "width": 15,
                            "fields": [
                                {
                                    "category": "D001 v1_11",
                                    "adr": "ADR1",
                                    "column": "mem1",
                                },
                            ]
                        },
                    {
                            "row": 4,
                            "width": 37,
                            "fields": [
                                {
                                    "category": "CALC",
                                    "adr": "PNK",
                                    "column": "Wp_KBTIi",
                                },
                                {
                                    "category": "CALC",
                                    "adr": "PNK",
                                    "column": "Wp_diss_pnki",
                                }
                            ]
                        }
                ]
            }
        ]
    }
    settings.setValue('graphs', graphs)
    filters = ['time']
    settings.setValue('leftMenuFilters', filters)
    mainSettings = {
        'theme': 'black',
        'jsonDir': 'templates/',
        'toolBar': 'left', 
        'openLastFile': True
    }
    settings.setValue('mainSettings', mainSettings)


def getPalette(color):
    if color == 'black':
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(60, 60, 60))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Link, QColor(43, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(215, 0, 64))
    else:
        palette = QPalette()
    return palette
