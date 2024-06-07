# Dual Choice (WIP)

Отдельный репозиторий, так как проект независим от приложения с автоулучшением фото.

Видеодемонстрация:

https://github.com/pyrogn/aaa-dual-choice/assets/60060559/d64a314c-48ae-4465-ad53-6c6c9f7625b3


## TODO

- [x] Make more stable index.html and backend (sometimes image updates twice)
- [x] Add async to postgres and redis
- [x] Add tests
- [x] Add script to calculate statistics    
- [x] Think of state when you will reload app (redis, db cleanings)
- [x] Fix security problems (exposed services and open passwords) (can be better)
- [ ] Add simple ddos protection (limits)
- [ ] Use github actions to deploy application?
- [ ] Fix tests again (to work within docker compose) and make sense out of docker containers.
- [x] Add some niceties (progress bar, better html)
