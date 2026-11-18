from todor import create_app


app = create_app({
    'AUTHZ_MODE': 'baseline',
    'DATABASE_URL': 'sqlite:///courseproject_demo.db',
})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=False)
