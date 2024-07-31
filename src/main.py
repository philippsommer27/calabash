import click
from analysis import analysis_runner
from experiment import runner

@click.group()
def cli():
    pass

@cli.command()
@click.argument('config')
def analyze(config):
    analysis_runner.run(config)

@cli.command()
@click.argument('config')
def experiment(config):
    runner.main(config)

if __name__ == "__main__":
    cli()