'use strict';

const gulp = require("gulp"),
    sass = require("gulp-sass"),
    clean = require('gulp-clean');

// set paths ...
const config = {
	scssPath: "src/scss",
	destPath: "application/static/stylesheets",
  imgDestPath: "application/static/govuk_template/images"
}

// Delete our old stylesheets files
gulp.task('clean-css', function () {
  return gulp.src('application/static/stylesheets/**/*', {read: false})
    .pipe(clean());
});

// compile scss to CSS
gulp.task("scss", ['clean-css', 'copy'], function() {
	return gulp.src( config.scssPath + '/*.scss')
	.pipe(sass({outputStyle: 'expanded',
		includePaths: [ 'src/govuk_frontend_toolkit/stylesheets',
			'application/static/govuk_template/stylesheets',
			'src/govuk_elements/assets/sass']})).on('error', sass.logError)
	.pipe(gulp.dest(config.destPath))
})

// Watch src folder for changes
gulp.task("watch", ["scss"], function () {
  gulp.watch("src/scss/**/*", ["scss"])
});

gulp.task('copy', function() {
  gulp.src('src/vendor/css/*.css')
    .pipe(gulp.dest(config.destPath));
  gulp.src('src/govuk_elements/assets/images/*.png')
    .pipe(gulp.dest(config.imgDestPath));
});

// Set watch as default task
gulp.task("default", ["watch"]);