from IPython.nbconvert.preprocessors import Preprocessor


class TableOfContents(Preprocessor):

    def preprocess(self, nb, resources):
        """Extract a table of contents from the cells, based on the headings
        in the cells."""

        # get the minimum heading level
        try:
            self.min_level = min(x.level for x in nb.worksheets[0].cells if x.cell_type == 'heading')
        except ValueError:
            self.min_level = 1

        resources['toc'] = []
        nb, resources = super(TableOfContents, self).preprocess(nb, resources)
        resources['toc'] = "\n".join(resources['toc'])

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        # skip non-heading cells
        if cell.cell_type != 'heading':
            return cell, resources

        # format the indentation and anchor link
        level = cell.level
        source = cell.source
        indent = "\t" * (level - self.min_level)
        link = '<a href="#{}">{}</a>'.format(
            source.replace(" ", "-"), source)
        resources['toc'].append("{}* {}".format(indent, link))

        return cell, resources
