import { Component, OnInit, Input, OnDestroy } from '@angular/core';
import { FormControl } from '@angular/forms';
import { Observable, combineLatest, Subscription, of } from 'rxjs';
import { map, startWith, switchMap, tap } from 'rxjs/operators';
import { DataFormService } from '../data-form.service';

/**
 *  Ce composant permet de créer un "input" de type "slider" affichant les niveau du diffusion disponible pour l'appli
 *
 * @example
 * <pnx-level-diffusion
 *   [parentFormControl]="FormControl"
 * </pnx-level-diffusion>
 */
@Component({
  selector: 'pnx-diffusion-level-form',
  templateUrl: 'diffusion-level-form.component.html',
  styleUrls: ['./diffusion-level-form.component.scss'],
})
export class DiffusionLevelFormComponent implements OnInit, OnDestroy {
  
  @Input() parentFormControl: FormControl;
  public levels: any[] = [];
  public levelSelected: number = 0;
  private _subscriptions: Subscription[] = [];

  constructor(
    private dataFormS: DataFormService,
  ) { }

  ngOnInit() {

    this._subscriptions.push(
      this.getLevels().subscribe((values: any[]) => this.levels = values)
    );

    this._subscriptions.push(
      combineLatest(
        this.getLevels(),
        this.parentFormControl.valueChanges
          .pipe(startWith(null))
      )
        .pipe(
          switchMap(([levels, formValue]) => {
            if (formValue === null) {
              return this.dataFormS.getDefaultNomenclatureValue(['NIV_PRECIS'])
                      .pipe(
                        map((values: any): number => values['NIV_PRECIS']),
                      );
            }
            return of(formValue);
          }),
          map((id_nomenclature: number): number => this.levels.findIndex(e => e.id_nomenclature === id_nomenclature)),
        )
        .subscribe((index: number) => this.levelSelected = index)
    );
  }

  getLevels(): Observable<any[]> {
    return this.dataFormS.getNomenclature('NIV_PRECIS', null, null, {orderby: 'hierarchy'})
      .pipe(
        map(data => data.values),
      );
  }

  getDescription() {
    return this.levels[this.levelSelected] ? this.levels[this.levelSelected].definition_default : '';
  }

  onChange(event) {
    this.parentFormControl.setValue(this.levels[event.value].id_nomenclature)
  }

  ngOnDestroy() {
    this._subscriptions.forEach(s => { s.unsubscribe(); });
  }
}
