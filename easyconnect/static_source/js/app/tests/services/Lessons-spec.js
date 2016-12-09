describe('Lessons Service tests', function () {
    var Lessons;

    // excuted before each "it" is run.
    beforeEach(function () {

        // load the module.
        module('ecApp');

        // inject your service for testing.
        // The _underscores_ are a convenience thing
        // so you can have your variable name be the
        // same as your injected service.
        inject(function (_Lessons_) {
            Lessons = _Lessons_;
        });
    });

    // check to see if it has the expected functions
    it('should have a get function', function () {
        expect(angular.isFunction(Lessons.get)).toBe(true);
    });

    it('should have a save function', function () {
        expect(angular.isFunction(Lessons.save)).toBe(true);
    });

    it('should have a save function', function () {
        expect(angular.isFunction(Lessons.update)).toBe(true);
    });


});