from collections import namedtuple


def get_actions_list() -> list:
    """
    Описатель actions

    Returns:
        list: список для создания actions
    """
    Action = namedtuple(
        'action', [
            'name', 'title', 'icon', 'tip', 'hotkey', 'checkable', 'connect'
        ]
    )
    list_action = [
        # file actions
        Action('clear_all_action', 'Очистить окно', ':x.svg',
               'Очистить все данные в программе.', None, False, 'clear_main_window'),
        Action('open_txt_action', 'Открыть *.txt', ':file-plus.svg',
               'Открыть txt файл с данными.', None, False, ('get_open_file_window', 'txt')),
        Action('open_pdd_action', 'Открыть *.pdd', ':file.svg',
               'Открыть pdd файл с данными.', None, False, ('get_open_file_window', 'csv')),
        Action('open_csv_action', 'Открыть *.csv', ':file-text.svg',
               'Открыть csv файл с данными.', None, False, ('get_open_file_window', 'pdd')),
        Action('open_gzip_action', 'Открыть *.gzip', ':github.svg',
               'Открыть gzip файл с данными.', 'Ctrl+O', False, 'open_gzip_file'),
        Action('save_gzip_action', 'Сохранить как *.gzip...', ':save.svg',
               'Сохранить данные в формате gzip', 'Ctrl+S', False, 'save_gzip_data'),
        Action('save_csv_action', 'Сохранить как *.csv...', ':file-text.svg',
               'Сохранить данные в формате csv', None, False, 'save_csv_data'),
        Action('exit_action', 'Закрыть приложение', ':log-out.svg',
               'Закрыть приложение навсегда', 'Ctrl+Q', False, 'close'),
        # service actions
        Action('calculate_data_action', 'Рассчитать данные', ':percent.svg',
               'Рассчитать данные для анализа', None, False, 'calculate_data'),
        Action('make_map_action', 'Создать карту', ':map.svg',
               'Создать интерактивную карту полёта', None, False, 'make_map'),
        Action('create_report_action', 'Создать отчёт', ':mail.svg',
               'Создать отчет по полету и сохранить его в xlsx', None, False, 'create_report'),
        Action('python_console_action', 'Python консоль', ':terminal',
               'Открыть окно консоли', None, False, 'python_console'),
        # view actions
        Action('hide_left_menu_action', 'Скрыть левое меню', ':eye-off',
               'Скрыть/показать левое меню', None, True, 'hide_left_menu'),
        Action('create_graph_action', 'Создать график', ':trending-up.svg',
               'Создать график в новом окне', None, False, 'create_graph'),
        Action('default_graph_action', 'Создать графики по умолчанию', ':shuffle.svg',
               'Создать графики по умолчанию в новых окнах', None, False, None),
        Action('cascade_action', 'Каскадное расположение', ':bar-chart.svg',
               'Каскадное расположение окон графиков', None, False, 'cascade_windows'),
        Action('horizontal_action', 'Горизонтальное расположение', ':more-vertical.svg',
               'Горизонтальное расположение окон графиков', None, True, 'horizontal_windows'),
        Action('vertical_action', 'Вертикальное расположение', ':more-horizontal.svg',
               'Вертикальное расположение окон графиков', None, True, 'vertical_windows'),
        Action('track_graph_action', 'Синхронизация графиков', ':move.svg',
               'Синхронизация всех графиков по оси Ох', None, True, 'track_graph'),
        Action('close_all_action', 'Закрыть все окна', ':x-circle.svg',
               'Закрыть все открытые окна', None, False, 'close_all_windows'),
        # settings actions
        Action('open_settings_actions', 'Настройки', ':settings.svg',
               'Меню настроек', None, False, 'open_settings'),
        Action('set_default_settings_actions', 'Установить стандартные настройки', ':sliders.svg',
               'Установить стандартные настройки', None, False, ['set_default_settings', True]),
        Action('load_settings_from_file_actions', 'Загрузить настройки из файла', ':download.svg',
               'Загрузить настройки из файла json', None, False, 'load_setting_from_file'),
        Action('save_settings_to_file_actions', 'Сохранить настройки в файл', ':save.svg',
               'Сохранить настройки в файл json', None, False, 'save_settings_to_file'),
        Action('about_action', 'О программе', ':help-circle.svg',
               'О программе', None, False, 'about')
    ]
    return list_action


def get_menu_dict() -> dict:
    """
    Описатель меню

    Returns:
        dict: словарь для создания меню
    """
    Submenu = namedtuple('submenu', ['title', 'icon'])
    menu_dict = {
        Submenu('Файл', None): [
            'clear_all_action',
            {
                Submenu('Открыть txt или cvs', ':file-plus.svg'): [
                    'open_txt_action',
                    'open_csv_action'
                ],
                Submenu('Открыть gzip или pdd', ':database.svg'): [
                    'open_pdd_action',
                    'open_gzip_action'
                ],
                Submenu('Сохранить как', ':save'): [
                    'save_gzip_action',
                    'save_csv_action'
                ]
            },
            'exit_action'
        ],
        Submenu('Просмотр', None): [
            'hide_left_menu_action',
            'create_graph_action',
            'default_graph_action',
            'cascade_action',
            'horizontal_action',
            'vertical_action',
            'track_graph_action',
            None,
            'close_all_action'
        ],
        Submenu('Сервисы', None): [
            'calculate_data_action',
            'make_map_action',
            'create_report_action',
            'python_console_action'
        ],
        Submenu('Настройки', None): [
            'open_settings_actions',
            'load_settings_from_file_actions',
            'save_settings_to_file_actions',
            'set_default_settings_actions',
            'about_action'
        ]
    }
    return menu_dict


def get_toolbar_list() -> list:
    """
    Описатель тулбара

    Returns:
        list: список для создания тулбара
    """
    list_toolbar = [
        'open_txt_action',
        'open_gzip_action',
        'save_gzip_action',
        None,
        'exit_action',
        None,
        'calculate_data_action',
        'python_console_action',
        None,
        'hide_left_menu_action',
        'create_graph_action',
        'default_graph_action',
        None,
        'spin_box',
        None,
        'cascade_action',
        'horizontal_action',
        'vertical_action',
        'track_graph_action',
        None,
        'close_all_action'
    ]
    return list_toolbar
