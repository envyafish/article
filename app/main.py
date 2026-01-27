if __name__ == '__main__':

    import uvicorn

    # 启动API接口
    uvicorn.run(app='app.api:app', host='0.0.0.0', port=8000, reload=False,
                log_level="error")







