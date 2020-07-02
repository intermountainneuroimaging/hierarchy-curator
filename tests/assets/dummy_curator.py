from custom_curator import curator


class Curator(curator.Curator):

    def curate_project(self, project):
        project.label = "Curated"

    def curate_subject(self, subject):
        subject.label = "Curated"

    def curate_session(self, session):
        session.label = "Curated"

    def curate_acquisition(self, acquisition):
        acquisition.label = "Curated"

    def curate_file(self, file):
        file.label = "Curated"

    def curate_analysis(self, analysis):
        analysis.label = "Curated"
