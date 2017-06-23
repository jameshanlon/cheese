from cheese.init_app import app, init_app, manager

if __name__ == '__main__':
    init_app(app)
    manager.run()
