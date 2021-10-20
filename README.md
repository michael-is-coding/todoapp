# ToDo app in pure Python


## Features:

- user is using application by typing commands to the terminal
- add todo item
- list todos items
- paging the list of items
- delete todo item
- mark todo item as done
- mark todo item as not done
- mark todo item as in progress


## How it is gonna work?

1st version: 

- Terminal app
- storing todos in a text file

2nd version: 

- Web app
- storing todos in SQLite DB


## Implementation details

- we store each todo item as one line in text file
- if item is done then it starts with "::done::"
- we load all todos from file into a list when app starts
- we then (later) write whole list back to the file
