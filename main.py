import os
import readline
import sys
from dataclasses import dataclass
from enum import Enum, unique, auto
from math import ceil
from functools import partial

PAGE_LEN = 5

FILE_NAME = 'todos.txt'

PREFIX_DONE = '::done::'
PREFIX_RM = '::rm::'
PREFIX_STARTED = '::started::'


@unique
class Action(Enum):
    UNDONE = 'undone'
    DONE = 'done'
    NEW = 'new'
    LIST = 'ls'
    EXIT = 'exit'
    HELP = 'help'
    RM = 'rm'
    NEXT = 'next'
    PREV = 'prev'
    START = 'start'
    STOP = 'stop'

    @staticmethod
    def item_actions():
        return [Action.DONE, Action.UNDONE, Action.RM, Action.START, Action.STOP]


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
            if not is_status(PREFIX_RM, todo):
                todo_file.write(todo)


def parse_item_action_from_user_input(user_input):
    # done 3 -> ' 3'
    # done3 -> '3'
    # doneblah -> 'blah'
    # we get slice starting from 5th letter which have index 6
    for item_action in Action.item_actions():
        if user_input.startswith(item_action.value):
            item_number_str = user_input[len(item_action.value):].strip()
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
    if user_input.strip() in [action.value for action in Action]:
        return Action(user_input.strip()), None

    return None, None


def display_text(item, count=None):
    if is_status(PREFIX_DONE, item):
        title = item.replace(PREFIX_DONE, "\u2713 ", 1)
    elif is_status(PREFIX_STARTED, item):
        title = item.replace(PREFIX_STARTED, "-> ", 1)
    else:
        title = item

    return f"({count}) {title}" if count else title


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
        if is_status(PREFIX_RM, item):
            continue
        title = display_text(item, count)

        print(title, end='')
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


def is_status(status, item):
    return item.startswith(status)


def set_status(status, item):
    statuses = [PREFIX_DONE, PREFIX_STARTED]

    for s in statuses:
        if is_status(s, item):
            if s == status:
                return None
            new_item = unset_status(s, item)
            return f"{status}{new_item}"

    return f"{status}{item}"


def unset_status(status, item):
    if is_status(status, item):
        return item[len(status):]

    return None


def show_help():
    print('Commands:\n'
          '"ls" to list your todos \n'
          '"new" to create a new todo item\n'
          '"exit" to exit a program.\n'
          '"done" and number of the item to mark item as done\n'
          '"undone" and number of the item to mark item as not done\n'
          '"start" and number of the item to mark item as in progress\n'
          '"stop" and number of the item to mark item as not started\n')


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
    if action == Action.LIST:
        list_todos(todos, context, ListAction.START)
    elif action == Action.NEXT:
        list_todos(todos, context, ListAction.NEXT)
    elif action == Action.PREV:
        list_todos(todos, context, ListAction.PREV)
    elif action == Action.NEW:
        new_todo(todos)
    elif action == Action.EXIT:
        sys.exit()
    elif action == Action.HELP:
        show_help()
    elif action == Action.DONE:
        process_done(item_index, todos)
    elif action == Action.UNDONE:
        process_undone(item_index, todos)
    elif action == Action.RM:
        process_rm(item_index, todos)
    elif action == Action.START:
        process_start(item_index, todos)
    elif action == Action.STOP:
        process_stop(item_index, todos)


def process_action(item_index, todos, action_fn, success_str='', no_action_str=''):
    if item_index is None:
        print('No item with such number')
        return

    item = todos[item_index]
    updated_item = action_fn(item)
    if updated_item is not None:
        todos[item_index] = updated_item
        save_todos(todos)
        print(success_str + ': ' + display_text(updated_item))
    else:
        print(no_action_str)


def process_start(item_index, todos):
    process_action(item_index, todos, partial(set_status, PREFIX_STARTED), 'Started', 'Already started.')


def process_stop(item_index, todos):
    process_action(item_index, todos, partial(unset_status, PREFIX_STARTED), 'Stopped', "Not started, can't stop.")


def process_rm(item_index, todos):
    process_action(item_index, todos, partial(set_status, PREFIX_RM), 'Removed', 'Already removed.')


def process_undone(item_index, todos):
    process_action(item_index, todos, partial(unset_status, PREFIX_DONE), 'Undone', "Not done, can't undone")


def process_done(item_index, todos):
    process_action(item_index, todos, partial(set_status, PREFIX_DONE), 'Marked as done', 'Already marked as done')


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
    run()
