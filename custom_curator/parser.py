"""Flywheel gear context parser"""


def parse_config(gear_context):
    """Return args"""
    analysis_id = gear_context.destination["id"]
    analysis = gear_context.client.get(analysis_id)
    project = gear_context.client.get(analysis.parent["id"])
    curator_path = gear_context.get_input_path("curator")
    input_file_one = gear_context.get_input_path("additional-input-one")
    input_file_two = gear_context.get_input_path("additional-input-two")
    input_file_three = gear_context.get_input_path("additional-input-three")
    input_files = {
        "input_file_one": input_file_one,
        "input_file_two": input_file_two,
        "input_file_three": input_file_three,
    }
    return project, curator_path, input_files
