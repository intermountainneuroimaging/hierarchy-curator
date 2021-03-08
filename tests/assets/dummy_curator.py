from flywheel_gear_toolkit.utils.curator import HierarchyCurator


class Curator(HierarchyCurator):
    def curate_project(self, project):
        project.update(label="Curated")

    def curate_subject(self, subject):
        subject.update(label="Curated")

    def curate_session(self, session):
        session.update(label="Curated")

    def curate_acquisition(self, acquisition):
        acquisition.update(label="Curated")

    def curate_file(self, file):
        pass

    def curate_analysis(self, analysis):
        pass
