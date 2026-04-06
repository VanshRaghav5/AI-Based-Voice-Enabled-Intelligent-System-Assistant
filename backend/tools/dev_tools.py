from backend.tools.starter_tools import (
    close_app,
    create_file,
    delete_file,
    delete_memory,
    download_file,
    get_running_apps,
    git_clone,
    git_pull,
    git_push,
    install_dependencies,
    list_directory,
    list_memory,
    move_file,
    open_app,
    open_project,
    open_url,
    read_file,
    recall_data,
    remember_data,
    restart_system,
    run_backend_server,
    run_command,
    run_frontend,
    search_files,
    search_google,
    search_youtube,
    set_volume,
    shutdown_system,
    take_screenshot,
    organize_folder,
    write_file,
)


def register_all_tools(registry):
    """Register the starter tool set in a flat action interface."""

    registry.register("open_app", open_app)
    registry.register("close_app", close_app)
    registry.register("get_running_apps", get_running_apps)
    registry.register("set_volume", set_volume)
    registry.register("shutdown_system", shutdown_system)
    registry.register("restart_system", restart_system)
    registry.register("take_screenshot", take_screenshot)

    registry.register("run_command", run_command)

    registry.register("list_directory", list_directory)
    registry.register("create_file", create_file)
    registry.register("read_file", read_file)
    registry.register("write_file", write_file)
    registry.register("delete_file", delete_file)
    registry.register("move_file", move_file)
    registry.register("search_files", search_files)
    registry.register("organize_folder", organize_folder)

    registry.register("open_project", open_project)
    registry.register("run_backend_server", run_backend_server)
    registry.register("run_frontend", run_frontend)
    registry.register("git_clone", git_clone)
    registry.register("git_pull", git_pull)
    registry.register("git_push", git_push)
    registry.register("install_dependencies", install_dependencies)

    registry.register("open_url", open_url)
    registry.register("search_google", search_google)
    registry.register("search_youtube", search_youtube)
    registry.register("download_file", download_file)

    registry.register("remember_data", remember_data)
    registry.register("recall_data", recall_data)
    registry.register("delete_memory", delete_memory)
    registry.register("list_memory", list_memory)
