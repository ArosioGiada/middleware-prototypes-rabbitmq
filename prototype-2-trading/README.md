### before compilation, you will need:
- linux bash (wsl on windows)
- npm, nvm, node
- mkcert
- rust, cargo, sqlx-cli

### steps to compile and run the system:
- all scripts must be executed from the root directory of the project, not from the directory with scripts itself
- run scripts/generate_cert.sh
- run scripts/reset_database.sh
- run scripts/build.sh
- open https://localhost:8080

### configuration
- to change chess board size, open compose.yaml file and change WIDTH and HEIGHT env variables