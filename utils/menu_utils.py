from typing import List

from PyInquirer import prompt

def list_menu_selector(qprompt: str, list_items: List[str]) -> str:
    """
    Display a list menu and prompt the user to select an item.

    Args:
        qprompt: The question prompt to display.
        list_items: The list of items to display in the menu.

    Returns:
        str: The selected item.
    """
    menu = prompt([
        {
            'type': 'list',
            'name': 'name',
            'message': qprompt,
            'choices': list_items,
        }
    ])
    return menu['name']