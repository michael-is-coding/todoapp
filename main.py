import os
import readline
import sys
from dataclasses import dataclass
from enum import Enum, unique, auto
from math import ceil

PAGE_LEN = 5

FILE_NAME = 'todos.txt'

PREFIX_DONE = '::done::'
PREFIX_RM = '::rm::'

# todo: This should really be an enum
ACTION_UNDONE = 'undone'
ACTION_DONE = 'done'
ACTION_NEW = 'new'
ACTION_LIST = 'ls'
ACTION_EXIT = 'exit'
ACTION_HELP = 'help'
ACTION_RM = 'rm'
ACTION_NEXT = 'next'
ACTION_PREV = 'prev'

ALL_ACTIONS = [ACTION_LIST, ACTION_NEW, ACTION_EXIT, ACTION_DONE, ACTION_UNDONE,
               ACTION_HELP, ACTION_RM, ACTION_NEXT, ACTION_PREV]

ITEM_ACTIONS = [ACTION_DONE, ACTION_UNDONE, ACTION_RM]


@unique
class ListAction(Enum):
    START = auto()
    NEXT = auto()
    PREV = auto()


# todo: We want to  make it a frozen datalass
@dataclass
class Context:
    page = 0


def load_todos():
    if os.path.isfile(FILE_NAME):
        with open(FILE_NAME, 'r+') as todo_file:
            return list(todo_file)

    return []


def save_todos(todo_list):
    with open(FILE_NAME, 'w+') as todo_file:
        for todo in todo_list:
            if not is_rm(todo):
                todo_file.write(todo)


def parse_item_action_from_user_input(user_input):
    # done 3 -> ' 3'
    # done3 -> '3'
    # doneblah -> 'blah'
    # we get slice starting from 5th letter which have index 6
    for item_action in ITEM_ACTIONS:
        if user_input.startswith(item_action):
            item_number_str = user_input[len(item_action):].strip()
            if item_number_str.isnumeric():
                item_number = int(item_number_str)
                return item_action, item_number - 1
            else:
                return item_action, None

    return None, None


def parse_action_and_item_index(user_input, todo_list):
    # todo: try to make this nicer
    item_action, item_index = parse_item_action_from_user_input(user_input)
    if item_action:
        if item_index is not None:
            if item_index < len(todo_list):
                return item_action, item_index
            else:
                return item_action, None
        else:
            return item_action, None

    if user_input.strip() in ALL_ACTIONS:
        return user_input.strip(), None

    return None, None


def is_done(item):
    return item.startswith(PREFIX_DONE)


def display_todos(todo_list, page, page_len, pages_count):
    start_index = (page - 1) * page_len
    end_index = page * page_len

    count = start_index
    printed_count = 0

    # todo: we slice by page_len but if there are removed items
    # in the slice we will print less than page_len
    for item in todo_list[start_index:end_index]:
        if printed_count >= 5:
            break
        count += 1
        title = item
        if is_rm(item):
            continue
        elif is_done(item):
            title = title.replace(PREFIX_DONE, "\u2713 ", 1)

        print(f"({count}) {title}", end='')
        printed_count += 1

    if printed_count:
        print(f'\nPage {page} of {pages_count}')
        if page == pages_count:
            print('This is the last page. Type "prev" to go to the previous page.')
        elif page == 1:
            print('Type "next" to go to the next page.')
        else:
            print('Type "next" to go to the next page. Type "prev" to go to the previous page.')
    else:
        print('No todos. Let\'s add some. Type "new".')


# todo: marking item as X is same code again
def mark_done(item):
    if not is_done(item):
        return f"{PREFIX_DONE}{item}"

    return None


# todo: unmarking
def mark_undone(item):
    if is_done(item):
        return item[len(PREFIX_DONE):]

    return None


def is_rm(item):
    return item.startswith(PREFIX_RM)


def mark_rm(item):
    if not is_rm(item):
        return f"{PREFIX_RM}{item}"

    return None


def show_help():
    print('Commands:\n'
          '"ls" to list your todos \n'
          '"new" to create a new todo item\n'
          '"exit" to exit a program.\n'
          '"done" and number of the item to mark item as done\n'
          '"undone" and number of the item to mark item as not done\n')


def list_todos(todo_list, context, list_action):
    pages_count = ceil(len(todo_list) / PAGE_LEN)

    # todo: make this whoel if/elif/else more compact
    if list_action == ListAction.START:
        page = 1
    else:
        page = context.page
        if page:
            if list_action == ListAction.NEXT:
                if page == pages_count:
                    print('There are no more pages.')
                    return
                page += 1
            elif list_action == ListAction.PREV:
                if page == 1:
                    print("You're on the first page already.")
                    return
                page -= 1
        else:
            print('There is no previous page use "ls" to list from beginning.')
            return

    display_todos(todo_list, page, PAGE_LEN, pages_count)
    context.page = page


def process_user_input(user_input, todos, context):
    action, item_index = parse_action_and_item_index(user_input, todos)

    if not action:
        print('Not a valid action')

    # todo: we edit context, we should rather make copy and return new context
    if action == ACTION_LIST:
        list_todos(todos, context, ListAction.START)
    elif action == ACTION_NEXT:
        list_todos(todos, context, ListAction.NEXT)
    elif action == ACTION_PREV:
        list_todos(todos, context, ListAction.PREV)
    elif action == ACTION_NEW:
        new_todo(todos)
    elif action == ACTION_EXIT:
        sys.exit()
    elif action == ACTION_HELP:
        show_help()
    elif action == ACTION_DONE:
        process_done(item_index, todos)
    elif action == ACTION_UNDONE:
        process_undone(item_index, todos)
    elif action == ACTION_RM:
        process_rm(item_index, todos)


def process_action(item_index, todos, action_fn, success_str='', no_action_str=''):
    if item_index is None:
        print('No item with such number')
        return

    item = todos[item_index]
    updated_item = action_fn(item)
    if updated_item is not None:
        todos[item_index] = updated_item
        save_todos(todos)
        print(success_str)
    else:
        print(no_action_str)


def process_rm(item_index, todos):
    process_action(item_index, todos, mark_undone, 'Removed.', 'Already removed.')


def process_undone(item_index, todos):
    process_action(item_index, todos, mark_undone, 'Undone.', "Not done, can't undone")


def process_done(item_index, todos):
    process_action(item_index, todos, mark_done, 'Marked as done.', 'Already marked as done')


def new_todo(todos):
    user_answer = input('Write your todo. Press enter when done.\n')
    todos.append(user_answer + '\n')
    save_todos(todos)
    print('Your todo is created')


def run():
    print('Welcome to our ToDo app.')
    show_help()
    todos = load_todos()
    context = Context()
    while 1:
        user_input = input()
        # todo: again, context is passed around and it is updated
        # we should give function context and it should return
        # updated context
        process_user_input(user_input, todos, context)
        print('Waiting for your next action. Type "help" to see available commands.\n')


if __name__ == '__main__':
    # run()
    import sys
    sys.stdout.write('\rsome todo to edit')
    # x = sys.stdout.readline.insert_text("hello")
    readline.insert_text("hello")
    import time
    time.sleep(100)
