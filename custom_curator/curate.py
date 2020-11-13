import argparse

import flywheel

from custom_curator import walker, utils


def get_curator(
    client, curator_path: utils.PathLike, write_report: bool = False ** kwargs
):
    """Returns an instantiated curator

    Args:
        client (flywheel.Client): The flywheel sdk client.
        curator_path (Path-like): A path to a curator module.
        **kwargs: Extra keyword arguments.
    """
    curator = utils.load_converter(curator_path).Curator()
    curator.client = client
    setattr(curator, "write_report", write_report)
    for k, v in kwargs.items():
        setattr(curator, k, v)
    return curator


def main(
    client: flywheel.Client,
    parent: utils.Container,
    curator_path: utils.PathLike,
    **kwargs
):
    """Curates a flywheel project using a curator.

    Args:
        client (flywheel.Client): The flywheel sdk client.
        project (flywheel.Project): The project to curate.
        curator_path (Path-like): A path to a curator module.
        kwargs (dict): Dictionary of attributes/value to set on curator.
    """
    curator = get_curator(client, curator_path, **kwargs)

    project_walker = walker.Walker(parent, depth_first=curator.depth_first)

    for container in project_walker.walk():
        curator.curate_container(container)


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(description="Argument parser for curation")
    parser.add_argument(
        "--api-key", default=None, help="Pass in api key if not logged in with cli"
    )
    parser.add_argument(
        "--curator", "-c", required=True, help="path to curator implementation"
    )
    parser.add_argument("--input-file-one", help="Input file one")
    parser.add_argument("--input-file-two", help="Input file two")
    parser.add_argument("--input-file-three", help="Input file three")
    parser.add_argument("path", help="The resolver path to the project")

    args = parser.parse_args()
    client = flywheel.Client(args.api_key)
    project = client.lookup(args.path)
    main(
        client,
        project,
        args.curator,
        input_file_one=args.input_file_one,
        input_file_two=args.input_file_two,
        input_file_three=args.input_file_three,
    )
